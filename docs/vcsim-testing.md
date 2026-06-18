# vCSIM Testing Guide

راهنمای کامل راه‌اندازی محیط تست با vCenter Simulator (vcsim) برای تست VCM

---

## چرا vcsim؟

همه کاربران به vCenter Server واقعی دسترسی ندارن. **vcsim** یه vCenter کامل رو شبیه‌سازی میکنه که:

- کاملاً رایگان و open-source هست (VMware/govmomi)
- همه vSphere API ها رو پشتیبانی میکنه
- توی Docker اجرا میشه — نیاز به ESXi نداره
- برای CI/CD مناسبه

---

## معماری

```
┌─────────────────────────────────────────────────────────┐
│  docker compose -f docker-compose.test.yml up -d        │
│                                                          │
│  ┌───────────────┐      ┌──────────────────────────┐    │
│  │  vcsim        │      │  VCM Backend (FastAPI)   │    │
│  │  port: 8989   │◄────►│  port: 8000              │    │
│  │               │      │                          │    │
│  │  2 DC         │      │  + PostgreSQL :5432      │    │
│  │  3 Cluster    │      │  + Redis      :6379      │    │
│  │  5 Host/Cl.   │      └──────────────────────────┘    │
│  │  ~90 VM       │                                       │
│  └───────────────┘      ┌──────────────────────────┐    │
│                          │  VCM Frontend (React)    │    │
│                          │  port: 3000              │    │
│                          └──────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
                    ▲
                    │ seed_vcsim.py
                    │ رندوم‌سازی اسم VM ها
```

---

## قدم ۱ — راه‌اندازی vcsim

### با Docker (ساده‌ترین روش)

```bash
docker run -d \
  --name vcsim \
  --restart unless-stopped \
  -p 8989:8989 \
  vmware/vcsim:latest \
  -l 0.0.0.0:8989 \
  -dc 2 \
  -cluster 3 \
  -host 5 \
  -vm 0
```

| پارامتر | مقدار | توضیح |
|---------|-------|-------|
| `-dc 2` | ۲ | تعداد Datacenter |
| `-cluster 3` | ۳ | Cluster در هر DC |
| `-host 5` | ۵ | Host در هر Cluster |
| `-vm 0` | ۰ | VM — اسکریپت seed میسازه |

> **نکته:** با `-vm 0` شروع کن تا اسکریپت seed_vcsim.py
> تعداد دقیق VM با اسم‌های سفارشی بسازه.

### بررسی وضعیت

```bash
docker logs vcsim
docker ps | grep vcsim
```

---

## قدم ۲ — راه‌اندازی VCM کامل

```bash
# کلون پروژه (اگه نداری)
git clone https://github.com/DavoudTeimouri/vsphere-compliance-manager.git
cd vsphere-compliance-manager

# ساخت و اجرای همه سرویس‌ها
docker compose -f docker-compose.test.yml up -d

# بررسی وضعیت
docker compose -f docker-compose.test.yml ps
```

صبر کن تا همه سرویس‌ها `healthy` بشن (حدود ۳۰ ثانیه):

```bash
docker compose -f docker-compose.test.yml ps
# NAME       STATUS
# vcsim      Up (healthy)
# postgres   Up (healthy)
# redis      Up (healthy)
# backend    Up
# frontend   Up
```

---

## قدم ۳ — Seed کردن vcsim با اسم‌های واقعی

```bash
pip install pyVmomi

# رندوم کامل (هر بار متفاوت)
python scripts/seed_vcsim.py

# با seed مشخص (قابل تکرار)
python scripts/seed_vcsim.py --seed 42

# با اسم‌های سفارشی
python scripts/seed_vcsim.py \
  --pattern "WEB APP DB CACHE WORKER BATCH" \
  --env "PROD DEV DR STG" \
  --count 8 \
  --seed 2026

# فقط نمایش بدون اعمال تغییر
python scripts/seed_vcsim.py --dry-run --seed 42
```

### خروجی نمونه

```
🌱 Using seed: 42
✓ Connected to vcsim at localhost:8989
  Version: 6.5.0

📊 vcsim inventory:
   Clusters: 6
   VMs (before rename): 0

🔧 Renaming VMs...

  Cluster: DC0_C0 (5 hosts)
    ✓ DC0_H0_VM0 → WEB-PROD-101
    ✓ DC0_H0_VM1 → WEB-PROD-102
    ✓ DC0_H0_VM2 → APP-DR-101
    ✓ DC0_H0_VM3 → DB-STG-101
    ✓ DC0_H0_VM4 → CACHE-PROD-101

  Cluster: DC0_C1 (5 hosts)
    ✓ DC0_H1_VM0 → WEB-PROD-201
    ...

═══════════════════════════════════════════════════════
✅ Seeding complete!
   Renamed: 90 VMs

📌 Add this vCenter connection in VCM Settings:
   Name:     vcsim-test
   Host:     localhost
   Port:     8989
   Username: user
   Password: pass
   SSL:      disabled

⚙️  Suggested patterns for VCM Settings → Patterns:
   VM Name: ^(WEB)-  →  matches WEB-PROD-101, WEB-DR-202, ...
   VM Name: ^(APP)-  →  matches APP-PROD-101, APP-DR-202, ...
═══════════════════════════════════════════════════════
```

---

## قدم ۴ — پیکربندی VCM

### ۴.۱ ورود به VCM

مرورگر: **http://localhost:3000**

```
Username: admin
Password: Admin@1234
```

### ۴.۲ اضافه کردن vcsim به عنوان vCenter

**Settings → vCenter Connections → Add Connection:**

```
Name:     vcsim-test
Host:     vcsim        (اسم container در Docker network)
Port:     8989
Username: user
Password: pass
SSL:      disabled
```

> اگه خارج از Docker هستی، از `localhost` به جای `vcsim` استفاده کن.

### ۴.۳ اضافه کردن Pattern ها

**Settings → Patterns → Add Pattern:**

| Name | Type | Regex |
|------|------|-------|
| Web Servers | vm_name | `^(WEB)-` |
| App Servers | vm_name | `^(APP)-` |
| DB Servers | vm_name | `^(DB)-` |
| Cache Servers | vm_name | `^(CACHE)-` |
| Worker Servers | vm_name | `^(WORKER)-` |
| Batch Servers | vm_name | `^(BATCH)-` |
| Prod Datastores | datastore | `^(LocalDS_)` |

---

## قدم ۵ — اجرای Analysis و تست سناریوها

**Analysis → Run Analysis → vcsim-test → Run**

### سناریوهای DRS که باید پوشش داده بشن

| سناریو | انتظار |
|--------|--------|
| گروه WEB با ۵ VM در Cluster با ۵ Host | ساخت Rule با ۴ VM (hosts-1) |
| گروه DB با ۱ VM | Skip — گزارش بده، Rule نسازه |
| گروه APP با ۸ VM در Cluster با ۳ Host | ۲ Rule — هر کدام ۲ VM |
| Rule قدیمی `VCM-AAR-*` موجود | پاک کن و دوباره بساز |
| Rule دستی موجود | دست نزن |

### سناریوهای Storage که باید پوشش داده بشن

| سناریو | انتظار |
|--------|--------|
| ۲ VM از گروه WEB روی یک Datastore | Violation گزارش بده |
| ISO mount مشترک | نادیده بگیر |
| VM با Hard Disk روی ۲ Datastore | Scattered VM گزارش بده |
| فقط ۱ Datastore موجود | اعلام کن امکان جداسازی نیست |

---

## تکرار تست با seed های مختلف

برای پوشش بیشتر سناریوها، با seed های مختلف تست کن:

```bash
for seed in 1 42 100 2026 9999; do
  echo "=== Testing with seed $seed ==="
  python scripts/seed_vcsim.py --seed $seed --count 6
  echo "Now run analysis in VCM and verify results"
  read -p "Press Enter to continue to next seed..."
done
```

---

## توقف محیط تست

```bash
# متوقف کردن
docker compose -f docker-compose.test.yml stop

# حذف کامل (شامل database)
docker compose -f docker-compose.test.yml down -v

# فقط vcsim رو restart کن (بدون از دست دادن database)
docker restart vcsim
python scripts/seed_vcsim.py --seed 42
```

---

## عیب‌یابی

### vcsim وصل نمیشه

```bash
# بررسی وضعیت container
docker logs vcsim

# تست مستقیم API
curl -k -u user:pass https://localhost:8989/sdk
```

### خطای SSL

```bash
# اطمینان از اینکه verify_ssl در VCM Settings خاموشه
# Settings → vCenter Connections → Edit → SSL: disabled
```

### VM ها بعد از restart vcsim پاک میشن

vcsim **stateless** هست — بعد از هر restart باید دوباره seed بزنی:

```bash
docker restart vcsim
sleep 5
python scripts/seed_vcsim.py --seed 42
```
