import arxiv
import openai
import PyPDF2
import pdf2image
import PIL
import schedule
import requests

def test_imports():
    print("所有依赖包导入成功！")
    print(f"PIL版本: {PIL.__version__}")
    print(f"PyPDF2版本: {PyPDF2.__version__}")
    
if __name__ == "__main__":
    test_imports()