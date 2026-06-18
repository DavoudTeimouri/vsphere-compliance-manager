# vcsim Testing Guide

راهنمای کامل تست VCM با vCenter Simulator — بدون نیاز به vCenter واقعی.

---

## ۱. معرفی vcsim

**vcsim** یک شبیه‌ساز vCenter Server هست که توسط VMware (govmomi) نوشته شده.
کامل‌ترین emulator موجود برای vSphere API هست و از pyVmomi کاملاً پشتیبانی میکنه.

**چه چیزهایی رو شبیه‌سازی میکنه:**
- Datacenter / Cluster / Host / VM
- Datastore / Datastore Cluster
- DRS Rules (Anti-Affinity / Affinity)
- vSphere API (SOAP/REST) کامل

**چه چیزهایی رو شبیه‌سازی **نمیکنه**:**
- Storage vMotion واقعی
- Network packet flow
- Performance metrics (با مقادیر ثابت جواب میده)

---

## ۲. راه‌اندازی سریع (Docker)

### الف) فقط vcsim

```bash
docker run -d --name vcsim \
  -p 8989:8989 \
  ghcr.io/vmware/govmomi/vcsim:latest \
  -httptest.serve=0.0.0.0:8989 \
  -dc 2 \
  -cluster 3 \
  -host 4 \
  -vm 20 \
  -ds 4 \
  -pod 2

# تست اتصال
curl -k https://localhost:8989/sdk
```

**پارامترهای مهم vcsim:**

| پارامتر | توضیح | پیشنهاد برای تست کامل |
|---------|-------|----------------------|
| `-dc N` | تعداد Datacenter | 2 |
| `-cluster N` | تعداد Cluster در هر DC | 3 |
| `-host N` | تعداد Host در هر Cluster | 4 |
| `-vm N` | تعداد VM در هر Host | 5 |
| `-ds N` | تعداد Datastore | 4 |
| `-pod N` | تعداد Datastore Cluster | 2 |
| `-pg N` | تعداد Port Group | 2 |

### ب) محیط کامل — vcsim + VCM

```bash
cd docs/vcsim

# بالا آوردن همه چیز
docker compose -f docker-compose.vcsim.yml up -d

# چک کردن وضعیت
docker compose -f docker-compose.vcsim.yml ps

# لاگ backend
docker compose -f docker-compose.vcsim.yml logs -f backend
```

بعد از اجرا:
- **UI**: http://localhost:3000 (admin / VCM@admin2024!)
- **API**: http://localhost:8000/docs
- **vcsim**: https://localhost:8989/sdk

---

## ۳. Seed کردن vcsim با نام‌های واقعی

vcsim اسم VM ها رو به صورت `DC0_H0_VM0` میسازه که با pattern های VCM match نمیشن.
از اسکریپت `seed_vcsim.py` استفاده کن تا اسم‌های واقعی و randomize بسازه:

### نصب پیش‌نیازها

```bash
pip install pyVmomi
```

### اجرای ساده (fully random)

```bash
python3 docs/vcsim/seed_vcsim.py
```

هر بار اجرا بشه نام‌های متفاوتی میسازه — seed رو نشون میده:

```
Seed: 1718623412  (use --seed 1718623412 to reproduce)
```

### اجرا با seed ثابت (reproducible)

```bash
python3 docs/vcsim/seed_vcsim.py --seed 42
```

### سناریوهای مختلف

```bash
# سناریو ۱: فقط Web و DB — ساده
python3 docs/vcsim/seed_vcsim.py \
  --prefixes WEB DB \
  --envs PROD DR

# سناریو ۲: محیط بزرگ با همه prefix ها
python3 docs/vcsim/seed_vcsim.py \
  --prefixes WEB APP DB CACHE PROXY WORKER BATCH MON \
  --envs PROD DR STG DEV

# سناریو ۳: dry-run اول ببین چی میشه
python3 docs/vcsim/seed_vcsim.py --dry-run --seed 99

# سناریو ۴: vcsim روی host دیگه
python3 docs/vcsim/seed_vcsim.py \
  --host 192.168.1.100 \
  --port 8989 \
  --seed 42
```

### خروجی نمونه

```
VCM vcsim Test Data Generator
========================================
Host:     localhost:8989
Prefixes: ['WEB', 'APP', 'DB', 'CACHE']
Envs:     ['PROD', 'DR']
Seed:     1718623412

✓ Connected to vcsim at localhost:8989
  Version: 7.0.0

Renaming 20 VMs:
  DC0_H0_VM0        → WEB-PROD-01
  DC0_H0_VM1        → APP-PROD-01
  DC0_H1_VM0        → DB-DR-01
  DC0_H1_VM1        → CACHE-PROD-01
  ...

============================================================
INVENTORY SUMMARY
============================================================
Cluster: DC0_C0  (4 hosts, 10 VMs)
  [APP]   2 VMs: APP-DR-01, APP-PROD-01
  [DB]    2 VMs: DB-DR-01, DB-PROD-01
  [WEB]   3 VMs: WEB-DR-01, WEB-PROD-01, WEB-PROD-02
  [CACHE] 3 VMs: CACHE-DR-01, CACHE-PROD-01, CACHE-PROD-02
```

---

## ۴. اتصال VCM به vcsim

بعد از seed کردن، توی UI یا API وصل بشو:

### از طریق UI

1. برو به **Settings → vCenter Connections → Add**
2. پر کن:
   - **Name**: vcsim-local
   - **Host**: `vcsim` (اگه Docker Compose باشه) یا `localhost`
   - **Port**: 8989
   - **Username**: user
   - **Password**: pass
   - **Verify SSL**: ❌ خاموش
3. کلیک **Test Connection** — باید سبز بشه
4. کلیک **Save**

### از طریق API

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"VCM@admin2024!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Add vcsim connection
curl -s -X POST http://localhost:8000/api/vcenter/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "vcsim-local",
    "host": "vcsim",
    "port": 8989,
    "username": "user",
    "password": "pass",
    "verify_ssl": false
  }'
```

---

## ۵. تنظیم Pattern ها برای تست

```bash
# اضافه کردن pattern های مناسب برای seed_vcsim.py
for pattern in \
  '{"name":"Web Servers","pattern_type":"vm_name","regex_pattern":"^(WEB)-"}' \
  '{"name":"App Servers","pattern_type":"vm_name","regex_pattern":"^(APP)-"}' \
  '{"name":"DB Servers","pattern_type":"vm_name","regex_pattern":"^(DB)-"}' \
  '{"name":"Cache Servers","pattern_type":"vm_name","regex_pattern":"^(CACHE)-"}' \
  '{"name":"Proxy Servers","pattern_type":"vm_name","regex_pattern":"^(PROXY)-"}' \
  '{"name":"Worker Servers","pattern_type":"vm_name","regex_pattern":"^(WORKER)-"}' \
  '{"name":"Prod Datastores","pattern_type":"datastore","regex_pattern":"^(DS-PROD)-"}' \
  '{"name":"DR Datastores","pattern_type":"datastore","regex_pattern":"^(DS-DR)-"}'; do
  curl -s -X POST http://localhost:8000/api/settings/patterns \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$pattern" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'  ✓ {d.get(\"name\",d)}')"
done
```

---

## ۶. سناریوهای تست کامل

### سناریو A — DRS Compliance

```bash
# ۱. seed با سناریوی DRS violation
python3 docs/vcsim/seed_vcsim.py \
  --prefixes WEB APP DB \
  --envs PROD PROD PROD \   # عمداً همه PROD تا تعداد بیشتر باشه
  --seed 100

# ۲. Run analysis
VCENTER_ID=1
curl -s -X POST http://localhost:8000/api/analysis/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"vcenter_id\": $VCENTER_ID, \"analysis_type\": \"drs\"}"

# ۳. بررسی findings
sleep 30
curl -s http://localhost:8000/api/analysis/1/findings \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

### سناریو B — Storage Compliance

```bash
# seed با تعداد datastore کم (تا violation ایجاد بشه)
python3 docs/vcsim/seed_vcsim.py --seed 200

# Run storage analysis
curl -s -X POST http://localhost:8000/api/analysis/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"vcenter_id\": 1, \"analysis_type\": \"storage\"}"
```

### سناریو C — Full Analysis با Apply

```bash
# Full analysis
RUN_ID=$(curl -s -X POST http://localhost:8000/api/analysis/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"vcenter_id": 1, "analysis_type": "full"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['run_id'])")

echo "Analysis run ID: $RUN_ID"
sleep 45

# Apply DRS rules (operator/admin only)
curl -s -X POST http://localhost:8000/api/analysis/$RUN_ID/apply-drs \
  -H "Authorization: Bearer $TOKEN"

# Export report
curl -s "http://localhost:8000/api/reports/$RUN_ID/export?format=json" \
  -H "Authorization: Bearer $TOKEN" \
  -o "report_$RUN_ID.json"

echo "Report saved to report_$RUN_ID.json"
```

---

## ۷. خاموش کردن

```bash
# فقط متوقف کردن
docker compose -f docs/vcsim/docker-compose.vcsim.yml down

# متوقف کردن + حذف volumes (شروع تمیز)
docker compose -f docs/vcsim/docker-compose.vcsim.yml down -v
```

---

## ۸. Troubleshooting

| مشکل | راه‌حل |
|------|--------|
| `Connection refused` | صبر کن vcsim کامل بیاد بالا (`docker logs vcm-vcsim`) |
| `SSL error` | مطمئن شو `verify_ssl: false` هست |
| `VM rename failed` | در vcsim rename بعضی وقت‌ها timeout میده — نادیده بگیر |
| `No findings` | Pattern ها رو چک کن — باید با اسم VM ها match بشن |
| Analysis stuck در `running` | لاگ backend رو چک کن: `docker logs vcm-test-backend` |
