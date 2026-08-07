from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorClient
import os
from bson import ObjectId

app = FastAPI(title="API de Produtos Automotivos", description="API de produtos com MongoDB.")

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.loja_automotiva
collection = db.produtos

class ProdutoBase(BaseModel):
    nome: str
    marca: str
    preco: float
    quantidade_estoque: int
    categoria: Optional[str] = None

class Produto(ProdutoBase):
    id: str = Field(alias="_id")

def format_produto(produto) -> dict:
    return {
        "_id": str(produto["_id"]),
        "nome": produto["nome"],
        "marca": produto["marca"],
        "preco": produto["preco"],
        "quantidade_estoque": produto["quantidade_estoque"],
        "categoria": produto.get("categoria")
    }

@app.get("/")
async def read_root():
    return {"mensagem": "Bem-vindo à API de Produtos Automotivos (MongoDB). Acesse /docs para ver a documentação."}

@app.get("/produtos", response_model=List[Produto])
async def listar_produtos():
    produtos = await collection.find().to_list(1000)
    return [format_produto(p) for p in produtos]

@app.get("/produtos/{produto_id}", response_model=Produto)
async def obter_produto(produto_id: str):
    if not ObjectId.is_valid(produto_id):
        raise HTTPException(status_code=400, detail="ID inválido")
        
    produto = await collection.find_one({"_id": ObjectId(produto_id)})
    if produto:
        return format_produto(produto)
    raise HTTPException(status_code=404, detail="Produto não encontrado")

@app.post("/produtos", response_model=Produto, status_code=201)
async def criar_produto(produto: ProdutoBase):
    produto_dict = produto.model_dump()
    result = await collection.insert_one(produto_dict)
    
    novo_produto = await collection.find_one({"_id": result.inserted_id})
    return format_produto(novo_produto)

@app.delete("/produtos/{produto_id}", status_code=204)
async def excluir_produto(produto_id: str):
    if not ObjectId.is_valid(produto_id):
        raise HTTPException(status_code=400, detail="ID inválido")
        
    result = await collection.delete_one({"_id": ObjectId(produto_id)})
    if result.deleted_count == 1:
        return
    raise HTTPException(status_code=404, detail="Produto não encontrado")
