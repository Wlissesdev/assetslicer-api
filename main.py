import cv2
import numpy as np
import io
import zipfile
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI(title="AssetSlicer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def extrair_assets_em_memoria(
    img_bytes: bytes,
    grid_rows: int,
    grid_cols: int,
    bg_r: int = 255,
    bg_g: int = 255,
    bg_b: int = 255,
    tolerancia: int = 15,
    erosao_iteracoes: int = 1,
    padding_seguranca: int = 50,
    padding_final: int = 10,
    prefix: str = "asset",
) -> dict[str, bytes]:
    """
    Lógica exata do ssesf.py, adaptada para rodar em memória (sem disco).
    Retorna um dict { nome_arquivo: bytes_png }.
    """
    # Decodifica imagem dos bytes
    nparr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

    if img is None:
        raise ValueError("Não foi possível decodificar a imagem.")

    # Garante canal Alpha (BGRA)
    if len(img.shape) == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGRA)
    elif img.shape[2] == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
    # Se já é BGRA, OK

    height, width = img.shape[:2]
    cell_width = width // grid_cols
    cell_height = height // grid_rows

    resultados = {}

    for row in range(grid_rows):
        for col in range(grid_cols):
            x1 = max(0, col * cell_width - padding_seguranca)
            y1 = max(0, row * cell_height - padding_seguranca)
            x2 = min(width, (col + 1) * cell_width + padding_seguranca)
            y2 = min(height, (row + 1) * cell_height + padding_seguranca)

            roi = img[y1:y2, x1:x2].copy()

            b, g, r, a = cv2.split(roi)

            # Máscara: pixels que NÃO são o fundo (dentro da tolerância cor configurável)
            dist = np.sqrt(
                (r.astype(np.int32) - bg_r) ** 2 +
                (g.astype(np.int32) - bg_g) ** 2 +
                (b.astype(np.int32) - bg_b) ** 2
            ).astype(np.float32)

            mask_inicial = np.where(dist < tolerancia, 0, 255).astype(np.uint8)

            # Encontra os contornos
            contours, _ = cv2.findContours(
                mask_inicial, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            if not contours:
                # Célula vazia — pula
                continue

            # Pega o maior contorno (o personagem/sprite)
            maior_contorno = max(contours, key=cv2.contourArea)

            # Cria silhueta base (molde duro)
            mascara_base = np.zeros_like(mask_inicial)
            cv2.drawContours(
                mascara_base, [maior_contorno], -1, 255, thickness=cv2.FILLED
            )

            # --- FILTRO ANTI-SERRILHADO (idêntico ao ssesf.py) ---

            # 1. Erosão: remove franja do fundo nas bordas
            kernel = np.ones((3, 3), np.uint8)
            mascara_encolhida = cv2.erode(
                mascara_base, kernel, iterations=erosao_iteracoes
            )

            # 2. Gaussian Blur: suaviza a borda para transição natural
            mascara_suave = cv2.GaussianBlur(mascara_encolhida, (3, 3), 0)

            # 3. Monta imagem final com máscara suave como canal Alpha
            roi_limpo = cv2.merge((b, g, r, mascara_suave))

            # --- FIM DO FILTRO ---

            # Enquadramento justo ao redor do sprite
            x, y, w, h = cv2.boundingRect(maior_contorno)

            fx1 = max(0, x - padding_final)
            fy1 = max(0, y - padding_final)
            fx2 = min(roi.shape[1], x + w + padding_final)
            fy2 = min(roi.shape[0], y + h + padding_final)

            asset_final = roi_limpo[fy1:fy2, fx1:fx2]

            # Codifica PNG em memória
            success, encoded = cv2.imencode(".png", asset_final)
            if success:
                nome = f"{prefix}_{row}_{col}.png"
                resultados[nome] = encoded.tobytes()

    return resultados


@app.post("/process")
async def process_image(
    file: UploadFile = File(...),
    rows: int = Form(3),
    cols: int = Form(3),
    bg_r: int = Form(255),
    bg_g: int = Form(255),
    bg_b: int = Form(255),
    tolerancia: int = Form(15),
    erosao: int = Form(1),
    padding_seguranca: int = Form(50),
    padding_final: int = Form(10),
    prefix: str = Form("asset"),
):
    """
    Recebe um spritesheet e retorna um ZIP com os assets separados,
    fundo removido, usando a lógica exata do ssesf.py (OpenCV).
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem.")

    img_bytes = await file.read()

    try:
        assets = extrair_assets_em_memoria(
            img_bytes=img_bytes,
            grid_rows=rows,
            grid_cols=cols,
            bg_r=bg_r,
            bg_g=bg_g,
            bg_b=bg_b,
            tolerancia=tolerancia,
            erosao_iteracoes=erosao,
            padding_seguranca=padding_seguranca,
            padding_final=padding_final,
            prefix=prefix,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    if not assets:
        raise HTTPException(
            status_code=422,
            detail="Nenhum asset encontrado. Verifique as configurações de grade e cor de fundo.",
        )

    # Empacota tudo em um ZIP em memória
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, data in assets.items():
            zf.writestr(nome, data)
    zip_buffer.seek(0)

    filename = f"{prefix}_assets.zip"
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/health")
def health():
    return {"status": "ok", "engine": "OpenCV + ssesf.py logic"}
