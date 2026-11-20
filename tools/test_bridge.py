import sys, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ["LEVEL3_SCENE_GRAPH"] = "1"
from engine import scene_graph_bridge as BR

OUT = Path("spike_tmp/bridge_test")
OUT.mkdir(parents=True, exist_ok=True)

# مشهد tool اختباري
sc = {
    "kind": "tool",
    "title_ar": "أولا: رسوم الانتقال",
    "subtitle": "اذهب إلى خيارات المطور",
}

p = BR.render_card(sc, 0, 1, 1080, 1920, OUT)
print(f"✅ {p}")
print(f"   size: {p.stat().st_size // 1024} KB")
print(f"   active: {BR.is_active()}")
