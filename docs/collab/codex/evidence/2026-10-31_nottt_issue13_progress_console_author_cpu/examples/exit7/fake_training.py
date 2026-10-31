import os
os.write(1,b'initializing fake model\n[rank1] warning\n[NoTTT][cpu_loader] {"wait_ms":3}\n[CorrectedV3][progress] step=1/30000 loss=1.25\n[CorrectedV3][train] {"iteration":1}\n[CorrectedV3][checkpoint] synthetic save event\n')
os.write(2,b"stderr Traceback: fake diagnostic\n")
raise SystemExit(7)
