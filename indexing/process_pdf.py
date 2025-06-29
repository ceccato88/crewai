#!/usr/bin/env python3
"""
Processador End-to-End para PDFs
Arquivo único que processa PDFs completos: Parse → Embeddings → Vector DB
Não depende de outras configurações ou importações externas.
"""

import base64
import glob
import json
import os
import time
from typing import Any, TypedDict

import requests
from dotenv import load_dotenv
from upstash_vector import Index, Vector

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# =============================================
# CLASSES DE CONFIGURAÇÃO
# =============================================


class LlamaConfig:
    def __init__(self):
        self.base_url = os.getenv("LLAMA_BASE_URL", "https://api.cloud.llamaindex.ai/api/parsing")
        # Suporta tanto LLAMA_API_TOKEN quanto LLAMA_TOKEN para compatibilidade
        self.token = os.getenv("LLAMA_API_TOKEN") or os.getenv("LLAMA_TOKEN", "")
        self.default_multimodal = (
            os.getenv("LLAMA_USE_MULTIMODAL", "true").lower() == "true"
        )
        self.default_model = os.getenv("LLAMA_MODEL_NAME", "openai-gpt-4-1")
        # Suporta tanto NUM_WORKERS quanto LLAMA_NUM_WORKERS para compatibilidade
        self.num_workers = int(
            os.getenv("NUM_WORKERS") or os.getenv("LLAMA_NUM_WORKERS", "4")
        )
        self.max_wait_time = int(os.getenv("LLAMA_MAX_WAIT_TIME", "600"))
        self.check_interval = int(os.getenv("LLAMA_CHECK_INTERVAL", "10"))
        self.verbose = os.getenv("LLAMA_VERBOSE", "true").lower() == "true"

        # Diretórios
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.images_dir = os.getenv(
            "LLAMA_IMAGES_DIR", os.path.join(os.path.dirname(base_dir), "pdf_images")
        )
        self.payload_dir = os.getenv(
            "LLAMA_PAYLOAD_DIR", os.path.join(base_dir, "assets", "payloads")
        )

        # Headers
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }


class VoyageConfig:
    def __init__(self):
        self.base_url = os.getenv(
            "VOYAGE_BASE_URL", "https://api.voyageai.com/v1/multimodalembeddings"
        )
        # Suporta tanto VOYAGE_API_KEY quanto VOYAGE_API_TOKEN para compatibilidade
        self.token = os.getenv("VOYAGE_API_KEY") or os.getenv("VOYAGE_API_TOKEN", "")
        self.default_model = os.getenv("VOYAGE_MODEL_NAME", "voyage-multimodal-3")

        # Diretórios
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.embeddings_dir = os.getenv(
            "VOYAGE_EMBEDDINGS_DIR", os.path.join(base_dir, "assets", "embeddings")
        )

        # Headers
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }


class UpstashConfig:
    def __init__(self):
        # Suporta tanto as variáveis REST quanto as normais para compatibilidade
        self.vector_url = os.getenv("UPSTASH_VECTOR_REST_URL") or os.getenv(
            "UPSTASH_VECTOR_URL", ""
        )
        self.vector_token = os.getenv("UPSTASH_VECTOR_REST_TOKEN") or os.getenv(
            "UPSTASH_VECTOR_TOKEN", ""
        )
        self.max_image_size = int(os.getenv("UPSTASH_MAX_IMAGE_SIZE", "1048576"))


# =============================================
# CONSTANTES
# =============================================


class Constants:
    # HTTP Status
    HTTP_OK = 200

    # Job Status
    JOB_SUCCESS = "SUCCESS"
    JOB_PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    JOB_ERROR = "ERROR"
    JOB_CANCELLED = "CANCELLED"
    JOB_IN_PROGRESS = ["IN_PROGRESS", "PENDING", "PROCESSING"]
    JOB_SUCCESS_STATES = [JOB_SUCCESS, JOB_PARTIAL_SUCCESS]

    # File defaults
    PDF_EXTENSION = ".pdf"
    PDF_EXTENSION_LENGTH = 4
    FALLBACK_DOCUMENT_NAME = "document"

    # Headers
    ACCEPT_IMAGE_JPEG = "image/jpeg"

    # Vector defaults
    EMPTY_CURSOR = ""
    RANGE_LIMIT = 1000
    BATCH_SIZE = 100

    # Voyage Settings
    MULTIMODAL_3_DIMENSIONS = 1024
    VOYAGE_DEFAULT_MODEL = "voyage-multimodal-3"


# =============================================
# TIPOS
# =============================================


class ProcessingResult(TypedDict):
    success: bool
    pdf_url: str | None
    doc_name: str | None
    llama_result: dict[str, Any] | None
    voyage_result: dict[str, Any] | None
    upstash_result: dict[str, Any] | None
    total_time: float
    error: str | None


# =============================================
# PROCESSADOR PRINCIPAL
# =============================================


class PDFProcessor:
    """Processador End-to-End completo para PDFs"""

    def __init__(self):
        self.llama_config = LlamaConfig()
        self.voyage_config = VoyageConfig()
        self.upstash_config = UpstashConfig()

        # Inicializa o índice Upstash
        self.upstash_index = Index(
            url=self.upstash_config.vector_url, token=self.upstash_config.vector_token
        )

        # Cria diretórios necessários
        os.makedirs(self.llama_config.images_dir, exist_ok=True)
        os.makedirs(self.llama_config.payload_dir, exist_ok=True)
        os.makedirs(self.voyage_config.embeddings_dir, exist_ok=True)

        self.verbose = self.llama_config.verbose

        if self.verbose:
            print("🚀 PDFProcessor inicializado com sucesso!")
            print(f"📁 Diretório de imagens: {self.llama_config.images_dir}")
            print(f"📁 Diretório de payloads: {self.llama_config.payload_dir}")
            print(f"📁 Diretório de embeddings: {self.voyage_config.embeddings_dir}")

    # =============================================
    # MÉTODOS LLAMA PARSE
    # =============================================

    def _extract_pdf_name(self, pdf_url: str) -> str:
        """Extrai o nome do arquivo PDF da URL"""
        try:
            filename = pdf_url.split("/")[-1]
            filename = filename.split("?")[0]
            if filename.lower().endswith(Constants.PDF_EXTENSION):
                filename = filename[: -Constants.PDF_EXTENSION_LENGTH]
            filename = "".join(
                c for c in filename if c.isalnum() or c in ("-", "_", ".")
            )
            return filename if filename else Constants.FALLBACK_DOCUMENT_NAME
        except:
            return Constants.FALLBACK_DOCUMENT_NAME

    def _clean_existing_files(self, pdf_name: str) -> None:
        """Remove arquivos existentes com o mesmo nome do PDF"""
        if not self.verbose:
            return

        files_removed = 0

        # Remove imagens existentes
        image_pattern = os.path.join(self.llama_config.images_dir, f"{pdf_name}_page_*")
        for img_file in glob.glob(image_pattern):
            try:
                os.remove(img_file)
                print(f"🗑️ Arquivo removido: {os.path.basename(img_file)}")
                files_removed += 1
            except Exception as e:
                print(f"❌ Erro ao remover imagem {img_file}: {e}")

        # Remove payload existente
        payload_file = os.path.join(self.llama_config.payload_dir, f"{pdf_name}.json")
        if os.path.exists(payload_file):
            try:
                os.remove(payload_file)
                print(f"🗑️ Arquivo removido: {os.path.basename(payload_file)}")
                files_removed += 1
            except Exception as e:
                print(f"❌ Erro ao remover payload {payload_file}: {e}")

        # Remove embeddings existentes
        embedding_file = os.path.join(
            self.voyage_config.embeddings_dir, f"{pdf_name}.json"
        )
        if os.path.exists(embedding_file):
            try:
                os.remove(embedding_file)
                print(f"🗑️ Arquivo removido: {os.path.basename(embedding_file)}")
                files_removed += 1
            except Exception as e:
                print(f"❌ Erro ao remover embedding {embedding_file}: {e}")

        if files_removed > 0:
            print(f"✅ {files_removed} arquivos removidos com sucesso")

    def _upload_pdf(self, pdf_url: str) -> dict[str, Any]:
        """Envia PDF para processamento na LlamaIndex Cloud"""
        url = f"{self.llama_config.base_url}/upload"

        data = {
            "use_vendor_multimodal_model": str(
                self.llama_config.default_multimodal
            ).lower(),
            "vendor_multimodal_model_name": self.llama_config.default_model,
            "input_url": pdf_url,
            "num_workers": self.llama_config.num_workers,
        }

        if self.verbose:
            print(f"📤 Enviando PDF: {pdf_url}")

        # Try form data instead of JSON
        headers_without_content_type = {
            "Authorization": f"Bearer {self.llama_config.token}",
        }
        response = requests.post(
            url, data=data, headers=headers_without_content_type, timeout=30
        )

        if response.status_code == Constants.HTTP_OK:
            result = response.json()
            job_id = result.get("id")
            if self.verbose:
                print(f"✅ Upload realizado com sucesso! Job ID: {job_id}")
            return result
        else:
            if self.verbose:
                print(f"❌ Erro no upload: {response.status_code}")
                print(response.text)
            response.raise_for_status()
            return {}  # This line satisfies mypy

    def _get_job_status(self, job_id: str) -> dict[str, Any]:
        """Consulta o status de um job"""
        url = f"{self.llama_config.base_url}/job/{job_id}"
        response = requests.get(url, headers=self.llama_config.headers, timeout=30)

        if response.status_code == Constants.HTTP_OK:
            result = response.json()
            status = result.get("status", "unknown")
            if self.verbose:
                print(f"🔍 Status do job {job_id}: {status}")
            return result
        else:
            if self.verbose:
                print(f"❌ Erro ao consultar status: {response.status_code}")
            response.raise_for_status()
            return {}  # This line satisfies mypy

    def _wait_for_completion(self, job_id: str) -> dict[str, Any]:
        """Aguarda a conclusão de um job"""
        if self.verbose:
            print(f"⏳ Aguardando conclusão do job {job_id}...")

        start_time = time.time()

        while time.time() - start_time < self.llama_config.max_wait_time:
            status_result = self._get_job_status(job_id)
            status = status_result.get("status", "unknown")

            if status == Constants.JOB_SUCCESS:
                if self.verbose:
                    print("✅ Job concluído com sucesso!")
                return status_result
            elif status == Constants.JOB_PARTIAL_SUCCESS:
                if self.verbose:
                    print("⚠️ Job concluído com sucesso parcial")
                return status_result
            elif status == Constants.JOB_ERROR:
                if self.verbose:
                    print("❌ Job falhou")
                return status_result
            elif status == Constants.JOB_CANCELLED:
                if self.verbose:
                    print("🚫 Job cancelado")
                return status_result
            elif status in Constants.JOB_IN_PROGRESS:
                if self.verbose:
                    print(f"⏳ Job em progresso: {status}")
                time.sleep(self.llama_config.check_interval)
            else:
                if self.verbose:
                    print(f"❓ Status desconhecido: {status}")
                time.sleep(self.llama_config.check_interval)

        if self.verbose:
            print(f"⏰ Timeout atingido em {self.llama_config.max_wait_time} segundos")
        return self._get_job_status(job_id)

    def _get_structured_output(self, job_id: str, pdf_name: str) -> dict[str, Any]:
        """Extrai dados estruturados, texto e imagens do PDF processado"""
        json_url = f"{self.llama_config.base_url}/job/{job_id}/result/json"

        if self.verbose:
            print(f"📊 Extraindo dados estruturados do job {job_id}...")

        response = requests.get(json_url, headers=self.llama_config.headers, timeout=60)

        if response.status_code != Constants.HTTP_OK:
            if self.verbose:
                print(
                    f"❌ Erro na API ao obter dados estruturados: {response.status_code}"
                )
            response.raise_for_status()

        result = response.json()
        voyage_inputs = []
        total_images_saved = 0

        if self.verbose:
            print(f"📄 Processando {len(result.get('pages', []))} páginas")

        for page in result.get("pages", []):
            page_number = page.get("page")
            content_blocks = []

            # Extrai o markdown da página
            markdown = page.get("md", "").strip()
            if markdown:
                content_blocks.append({"type": "text", "text": markdown})

            # Processa todas as imagens da página
            for img in page.get("images", []):
                original_image_name = img["name"]
                image_extension = original_image_name.split(".")[-1]
                new_image_name = f"{pdf_name}_page_{page_number}.{image_extension}"

                img_url = f"{self.llama_config.base_url}/job/{job_id}/result/image/{original_image_name}"
                img_headers = {
                    "Accept": Constants.ACCEPT_IMAGE_JPEG,
                    "Authorization": f"Bearer {self.llama_config.token}",
                }

                try:
                    if self.verbose:
                        print(
                            f"📸 Baixando imagem: {original_image_name} -> {new_image_name}"
                        )

                    img_response = requests.get(
                        img_url, headers=img_headers, timeout=30
                    )
                    img_response.raise_for_status()

                    img_data = img_response.content
                    img_b64 = base64.b64encode(img_data).decode("utf-8")
                    img_path = os.path.join(
                        self.llama_config.images_dir, new_image_name
                    )

                    # Salva a imagem em disco
                    with open(img_path, "wb") as f:
                        f.write(img_data)

                    if os.path.exists(img_path):
                        file_size = os.path.getsize(img_path)
                        if self.verbose:
                            print(
                                f"✅ Imagem salva: {new_image_name} ({file_size} bytes)"
                            )
                        total_images_saved += 1

                    # Adiciona a imagem como base64 no bloco de conteúdo
                    content_blocks.append(
                        {
                            "type": "image_base64",
                            "image_base64": f"data:image/jpeg;base64,{img_b64}",
                        }
                    )

                except Exception as e:
                    if self.verbose:
                        print(f"❌ Erro ao processar imagem {original_image_name}: {e}")

            # Só adiciona se houver conteúdo
            if content_blocks:
                voyage_inputs.append({"content": content_blocks})

        # Salva o payload para VoyageAI
        payload = {
            "inputs": voyage_inputs,
            "model": Constants.VOYAGE_DEFAULT_MODEL,
            "truncation": False,
        }

        payload_filename = f"{pdf_name}.json"
        payload_path = os.path.join(self.llama_config.payload_dir, payload_filename)

        with open(payload_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)

        if self.verbose:
            print(f"💾 Payload salvo: {payload_path}")
            print("✅ Processamento concluído!")
            print(f"📄 Páginas processadas: {len(voyage_inputs)}")
            print(f"🖼️ Imagens salvas: {total_images_saved}")

        return {
            "original_result": result,
            "voyage_inputs": voyage_inputs,
            "total_images": total_images_saved,
            "payload_path": payload_path,
            "pdf_name": pdf_name,
        }

    def process_llama(self, pdf_url: str) -> dict[str, Any]:
        """Processa PDF completo com LlamaIndex"""
        pdf_name = self._extract_pdf_name(pdf_url)

        if self.verbose:
            print("🚀 Iniciando processamento LlamaIndex")
            print(f"🗂️ Verificando arquivos existentes para: {pdf_name}")

        self._clean_existing_files(pdf_name)

        # Upload
        upload_result = self._upload_pdf(pdf_url)
        job_id = upload_result.get("id")

        if not job_id:
            raise ValueError("Job ID não encontrado na resposta")

        # Aguarda conclusão
        status_result = self._wait_for_completion(job_id)
        if status_result.get("status") not in Constants.JOB_SUCCESS_STATES:
            raise RuntimeError(
                f"Job falhou ou não foi concluído: {status_result.get('status')}"
            )

        # Extrai dados estruturados
        return self._get_structured_output(job_id, pdf_name)

    # =============================================
    # MÉTODOS VOYAGE AI
    # =============================================

    def _get_embeddings(self, payload_path: str, pdf_name: str) -> dict[str, Any]:
        """Gera embeddings a partir de um arquivo payload"""
        if not os.path.exists(payload_path):
            raise FileNotFoundError(f"Arquivo payload não encontrado: {payload_path}")

        if self.verbose:
            print(f"📂 Carregando payload: {payload_path}")

        with open(payload_path, encoding="utf-8") as f:
            payload = json.load(f)

        if self.verbose:
            print("🔧 Gerando embeddings...")
            print(f"📊 Processando {len(payload.get('inputs', []))} entradas")

        response = requests.post(
            self.voyage_config.base_url,
            headers=self.voyage_config.headers,
            json=payload,
            timeout=60,
        )

        if response.status_code == Constants.HTTP_OK:
            result = response.json()
            if self.verbose:
                print("✅ Embeddings gerados com sucesso!")

            # Salva a resposta
            output_file = os.path.join(
                self.voyage_config.embeddings_dir, f"{pdf_name}.json"
            )
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            if self.verbose:
                print(f"💾 Embeddings salvos: {output_file}")

            # Estatísticas
            embeddings_data = result.get("data", [])
            if self.verbose:
                print(f"📈 Total de embeddings: {len(embeddings_data)}")
                if embeddings_data:
                    embedding_dim = len(embeddings_data[0].get("embedding", []))
                    print(f"📏 Dimensão dos embeddings: {embedding_dim}")

                    if embedding_dim != Constants.MULTIMODAL_3_DIMENSIONS:
                        print(
                            f"⚠️ Dimensão inesperada! Esperado: {Constants.MULTIMODAL_3_DIMENSIONS}, Atual: {embedding_dim}"
                        )

            return {
                "response": result,
                "output_file": output_file,
                "total_embeddings": len(embeddings_data),
                "pdf_name": pdf_name,
            }
        else:
            if self.verbose:
                print(f"❌ Erro na API: {response.status_code}")
                print(f"📄 Resposta: {response.text}")
            response.raise_for_status()
            return {}  # This line satisfies mypy

    def process_voyage(self, pdf_name: str) -> dict[str, Any]:
        """Processa embeddings a partir de um payload gerado pelo LlamaIndex"""
        payload_file = os.path.join(self.llama_config.payload_dir, f"{pdf_name}.json")

        if not os.path.exists(payload_file):
            raise FileNotFoundError(f"❌ Arquivo não encontrado: {payload_file}")

        if self.verbose:
            print(f"🔄 Processando payload do LlamaClient: {pdf_name}")

        return self._get_embeddings(payload_file, pdf_name)

    # =============================================
    # MÉTODOS UPSTASH
    # =============================================

    def _check_existing_vectors(self, doc_source: str) -> list[str]:
        """Verifica se já existem vetores para o documento"""
        try:
            if self.verbose:
                print("🔍 Verificando vetores existentes...")

            result = self.upstash_index.range(
                cursor=Constants.EMPTY_CURSOR,
                limit=Constants.RANGE_LIMIT,
                include_vectors=False,
                include_metadata=True,
                include_data=False,
            )

            existing_ids = []

            # Processa primeira página
            for vector in result.vectors:
                if vector.metadata and vector.metadata.get("doc_source") == doc_source:
                    existing_ids.append(vector.id)

            # Continua se houver mais páginas
            while result.next_cursor and result.next_cursor != Constants.EMPTY_CURSOR:
                result = self.upstash_index.range(
                    cursor=result.next_cursor,
                    limit=Constants.RANGE_LIMIT,
                    include_vectors=False,
                    include_metadata=True,
                    include_data=False,
                )

                for vector in result.vectors:
                    if (
                        vector.metadata
                        and vector.metadata.get("doc_source") == doc_source
                    ):
                        existing_ids.append(vector.id)

            if self.verbose:
                if existing_ids:
                    print(
                        f"📈 {len(existing_ids)} vetores encontrados para documento: {doc_source}"
                    )
                else:
                    print(f"📄 Nenhum vetor encontrado para documento: {doc_source}")

            return existing_ids

        except Exception as e:
            if self.verbose:
                print(f"❌ Erro ao consultar vetores: {e}")
            return []

    def _delete_existing_vectors(self, vector_ids: list[str]) -> bool:
        """Remove vetores existentes do banco"""
        if not vector_ids:
            return True

        try:
            if self.verbose:
                print("🗑️ Removendo vetores existentes...")

            batch_size = Constants.BATCH_SIZE
            total_deleted = 0

            for i in range(0, len(vector_ids), batch_size):
                batch = vector_ids[i : i + batch_size]
                result = self.upstash_index.delete(ids=batch)
                total_deleted += result.deleted

            if self.verbose:
                print(f"✅ {total_deleted} vetores removidos com sucesso")
            return True

        except Exception as e:
            if self.verbose:
                print(f"❌ Erro ao remover vetores: {e}")
            return False

    def _prepare_vectors_from_data(
        self,
        embeddings_data: dict[str, Any],
        payload_data: dict[str, Any],
        doc_source: str,
    ) -> list[Vector]:
        """Prepara vetores a partir dos dados de embeddings e payload"""
        vectors = []
        data_list = embeddings_data.get("data", [])
        inputs = payload_data.get("inputs", [])

        if self.verbose:
            print(f"📊 Processando {len(data_list)} entradas")

        for i, item in enumerate(data_list):
            vector_id = f"{doc_source}_{i}"
            embedding = item.get("embedding", [])

            # Extrai dados do payload correspondente
            text_content = ""
            image_data = {}

            if i < len(inputs):
                content_list = inputs[i].get("content", [])

                for content_item in content_list:
                    if content_item.get("type") == "text":
                        text_content = content_item.get("text", "")
                    elif content_item.get("type") == "image_base64":
                        # Sempre usa referência de imagem para evitar problemas de tamanho
                        image_filename = f"{doc_source}_page_{i + 1}.jpg"
                        image_path = os.path.join(
                            self.llama_config.images_dir, image_filename
                        )
                        image_data = {
                            "image_is_reference": True,
                            "image_reference": image_filename,
                            "image_path": image_path,
                        }
                        if self.verbose:
                            print(f"🖼️ Usando referência de imagem: {image_filename}")

            # Prepara metadados completos
            metadata = {
                "doc_source": doc_source,
                "page_number": i + 1,
                "text": text_content,
                **image_data,
            }

            # Cria vetor
            vector = Vector(id=vector_id, vector=embedding, metadata=metadata)
            vectors.append(vector)

        return vectors

    def process_upstash(self, doc_source: str) -> dict[str, Any]:
        """Insere vetores no banco para um documento específico"""
        if self.verbose:
            print("🚀 Iniciando processamento de vetores")
            print("📋 Verificando pré-requisitos...")

        # Verifica se payload existe
        payload_path = os.path.join(self.llama_config.payload_dir, f"{doc_source}.json")
        if not os.path.exists(payload_path):
            error_msg = "Payload não encontrado. Execute primeiro o LlamaClient"
            if self.verbose:
                print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

        # Verifica se embeddings existem
        embeddings_path = os.path.join(
            self.voyage_config.embeddings_dir, f"{doc_source}.json"
        )
        if not os.path.exists(embeddings_path):
            error_msg = "Embeddings não encontrados. Execute primeiro o VoyageClient"
            if self.verbose:
                print(f"❌ {error_msg}")
            return {"success": False, "error": error_msg}

        # Remove vetores existentes se houver
        existing_ids = self._check_existing_vectors(doc_source)
        if existing_ids:
            self._delete_existing_vectors(existing_ids)

        # Carrega dados
        if self.verbose:
            print(f"📂 Carregando arquivo de embeddings: {embeddings_path}")

        with open(embeddings_path, encoding="utf-8") as f:
            embeddings_data = json.load(f)

        with open(payload_path, encoding="utf-8") as f:
            payload_data = json.load(f)

        # Prepara vetores
        vectors = self._prepare_vectors_from_data(
            embeddings_data, payload_data, doc_source
        )

        if not vectors:
            raise ValueError("Nenhum vetor foi preparado")

        try:
            # Insere vetores
            if self.verbose:
                print(f"📤 Inserindo {len(vectors)} vetores no banco")

            batch_size = Constants.BATCH_SIZE
            total_upserted = 0

            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                self.upstash_index.upsert(vectors=batch)
                total_upserted += len(batch)

            if self.verbose:
                print(f"✅ {total_upserted} vetores inseridos com sucesso")
                print("✅ PROCESSAMENTO DE VETORES CONCLUÍDO!")

            return {
                "doc_source": doc_source,
                "total_vectors": total_upserted,
                "embeddings_file": embeddings_path,
                "payload_file": payload_path,
                "success": True,
            }

        except Exception as e:
            if self.verbose:
                print(f"❌ Erro ao inserir vetores: {e}")
            raise

    # =============================================
    # MÉTODO PRINCIPAL END-TO-END
    # =============================================

    def process_pdf_complete(
        self, pdf_url: str, doc_name: str | None = None
    ) -> ProcessingResult:
        """
        Processa PDF completo: LlamaIndex → VoyageAI → Upstash

        Args:
            pdf_url: URL do PDF para processar
            doc_name: Nome personalizado para o documento (opcional)

        Returns:
            Resultado completo do processamento
        """
        start_time = time.time()

        if self.verbose:
            print("🚀 INICIANDO PROCESSAMENTO COMPLETO END-TO-END")
            print(f"📄 PDF URL: {pdf_url}")
            if doc_name:
                print(f"📝 Nome do documento: {doc_name}")
            print("=" * 80)

        result: ProcessingResult = {
            "success": False,
            "pdf_url": pdf_url,
            "doc_name": doc_name,
            "llama_result": None,
            "voyage_result": None,
            "upstash_result": None,
            "total_time": 0,
            "error": None,
        }

        try:
            # ============ ETAPA 1: LLAMA INDEX ============
            if self.verbose:
                print("\n📋 ETAPA 1/3: Processamento LlamaIndex (Parse PDF)")
                print("=" * 60)

            try:
                llama_result = self.process_llama(pdf_url)
                result["llama_result"] = llama_result
                result["doc_name"] = llama_result.get("pdf_name", doc_name)

                if self.verbose:
                    print("✅ ETAPA 1 CONCLUÍDA")
                    print("-" * 30)

            except Exception as e:
                error_msg = str(e)
                if self.verbose:
                    print(f"❌ ETAPA 1 FALHOU: {error_msg}")
                    print("-" * 30)
                result["error"] = f"Etapa 1 (LlamaIndex): {error_msg}"
                return result

            # ============ ETAPA 2: VOYAGE AI ============
            if self.verbose:
                print("\n📋 ETAPA 2/3: Geração de Embeddings (VoyageAI)")
                print("=" * 60)

            try:
                doc_name = result["doc_name"]
                if not doc_name:
                    raise ValueError("Nome do documento não encontrado")
                voyage_result = self.process_voyage(doc_name)
                result["voyage_result"] = voyage_result

                if self.verbose:
                    print("✅ ETAPA 2 CONCLUÍDA")
                    print("-" * 30)

            except Exception as e:
                error_msg = str(e)
                if self.verbose:
                    print(f"❌ ETAPA 2 FALHOU: {error_msg}")
                    print("-" * 30)
                result["error"] = f"Etapa 2 (VoyageAI): {error_msg}"
                return result

            # ============ ETAPA 3: UPSTASH ============
            if self.verbose:
                print("\n📋 ETAPA 3/3: Inserção no Banco Vetorial (Upstash)")
                print("=" * 60)

            try:
                doc_name = result["doc_name"]
                if not doc_name:
                    raise ValueError("Nome do documento não encontrado")
                upstash_result = self.process_upstash(doc_name)
                result["upstash_result"] = upstash_result

                if self.verbose:
                    print("✅ ETAPA 3 CONCLUÍDA")
                    print("-" * 30)

            except Exception as e:
                error_msg = str(e)
                if self.verbose:
                    print(f"❌ ETAPA 3 FALHOU: {error_msg}")
                    print("-" * 30)
                result["error"] = f"Etapa 3 (Upstash): {error_msg}"
                return result

            # ============ SUCESSO COMPLETO ============
            result["success"] = True
            result["total_time"] = time.time() - start_time

            if self.verbose:
                print("\n🎉 PROCESSAMENTO END-TO-END CONCLUÍDO COM SUCESSO!")
                self._print_summary(result)

            return result

        except Exception as e:
            result["error"] = f"Erro geral no pipeline: {str(e)}"
            result["total_time"] = time.time() - start_time
            if self.verbose:
                print("\n💥 PROCESSAMENTO END-TO-END FALHOU")
                print(f"❌ Erro: {result['error']}")
            return result

    def _print_summary(self, result: ProcessingResult) -> None:
        """Imprime resumo do processamento"""
        print("\n📊 RESUMO DO PROCESSAMENTO:")
        print("=" * 50)

        print(f"📄 Documento: {result['doc_name']}")
        print(f"⏱️ Tempo total: {result['total_time']:.2f} segundos")

        # Status das etapas
        print("\n📋 STATUS DAS ETAPAS:")

        # Etapa 1
        if result["llama_result"]:
            pages = len(result["llama_result"].get("voyage_inputs", []))
            images = result["llama_result"].get("total_images", 0)
            print(f"  1️⃣ LlamaIndex: ✅ {pages} páginas, {images} imagens")

        # Etapa 2
        if result["voyage_result"]:
            embeddings = result["voyage_result"].get("total_embeddings", 0)
            print(f"  2️⃣ VoyageAI: ✅ {embeddings} embeddings gerados")

        # Etapa 3
        if result["upstash_result"]:
            vectors = result["upstash_result"].get("total_vectors", 0)
            print(f"  3️⃣ Upstash: ✅ {vectors} vetores inseridos")

        print("\n✅ PROCESSAMENTO CONCLUÍDO!")


# =============================================
# FUNÇÕES DE CONVENIÊNCIA
# =============================================


def process_pdf_from_url(
    pdf_url: str, doc_name: str | None = None, verbose: bool = True
) -> ProcessingResult:
    """
    Função de conveniência para processar um PDF a partir da URL

    Args:
        pdf_url: URL do PDF para processar
        doc_name: Nome personalizado para o documento (opcional)
        verbose: Se deve exibir logs detalhados

    Returns:
        Resultado completo do processamento
    """
    processor = PDFProcessor()
    processor.verbose = verbose
    return processor.process_pdf_complete(pdf_url, doc_name)


def process_existing_document(
    doc_name: str, step: str = "all", verbose: bool = True
) -> dict[str, Any]:
    """
    Função de conveniência para processar documento já existente

    Args:
        doc_name: Nome do documento (sem extensão)
        step: Etapa a executar ("voyage", "upstash", ou "all" para voyage+upstash)
        verbose: Se deve exibir logs detalhados

    Returns:
        Resultado do processamento
    """
    processor = PDFProcessor()
    processor.verbose = verbose

    if step == "voyage":
        result = processor.process_voyage(doc_name)
        result["success"] = True  # Se chegou aqui, foi bem-sucedido
        return result
    elif step == "upstash":
        return processor.process_upstash(doc_name)
    elif step == "all":
        try:
            voyage_result = processor.process_voyage(doc_name)
            upstash_result = processor.process_upstash(doc_name)
            return {
                "success": True,
                "voyage_result": voyage_result,
                "upstash_result": upstash_result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }
    else:
        raise ValueError("step deve ser 'voyage', 'upstash' ou 'all'")


# =============================================
# EXEMPLO DE USO
# =============================================

if __name__ == "__main__":
    # Processar PDF usando URL das variáveis de ambiente
    pdf_url = os.getenv("SAMPLE_PDF_URL")
    
    if not pdf_url:
        print("❌ Erro: Variável de ambiente SAMPLE_PDF_URL não encontrada")
        print("📝 Configure a URL do PDF na variável de ambiente SAMPLE_PDF_URL")
        exit(1)
    
    try:
        result = process_pdf_from_url(pdf_url)
        
        if result["success"]:
            print(f"✅ Processamento concluído: {result['doc_name']}")
        else:
            print(f"❌ Erro: {result['error']}")
            
    except Exception as e:
        print(f"💥 Erro crítico: {e}")
