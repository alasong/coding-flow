from typing import List, Dict, Any


class FrontendScaffolderAgent:
    def __init__(self, name: str = "前端脚手架生成"):
        self.name = name

    async def generate(self, software_units: List[Dict[str, Any]], work_packages: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
        import os
        base = os.path.join(output_dir, "project_code", "frontend")
        os.makedirs(base, exist_ok=True)
        html = (
            "<!doctype html>\n"
            "<html>\n"
            "<head><meta charset='utf-8'><title>UI</title><style>body{font-family:Arial;margin:20px}nav a{margin-right:10px}section{margin-top:20px}</style></head>\n"
            "<body>\n"
            "<nav>\n"
            "<a href='#home'>首页</a>"
            "<a href='#products'>商品</a>"
            "<a href='#cart'>购物车</a>"
            "<a href='#orders'>订单</a>"
            "<a href='#profile'>个人中心</a>\n"
            "</nav>\n"
            "<div id='content'></div>\n"
            "<script>\n"
            "function render(){const h=location.hash||'#home';const c=document.getElementById('content');if(h=='#home'){c.innerHTML='<h2>首页</h2><div id=health></div>';fetch('/health').then(r=>r.json()).then(j=>{document.getElementById('health').innerText='健康状态: '+j.status})}else if(h=='#products'){c.innerHTML='<h2>商品</h2><p>这里展示商品列表</p>'}else if(h=='#cart'){c.innerHTML='<h2>购物车</h2><p>这里管理购物车</p>'}else if(h=='#orders'){c.innerHTML='<h2>订单</h2><p>这里查看订单</p>'}else if(h=='#profile'){c.innerHTML='<h2>个人中心</h2><p>这里管理个人信息</p>'}}window.addEventListener('hashchange',render);render();\n"
            "</script>\n"
            "</body></html>\n"
        )
        with open(os.path.join(base, "index.html"), "w", encoding="utf-8") as f:
            f.write(html)
        return {"frontend": ["frontend/index.html"]}

