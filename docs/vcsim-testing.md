# Testing with vcsim

[vcsim](https://github.com/vmware/govmomi/tree/main/vcsim) یک شبیه‌ساز vCenter است که بدون نیاز به محیط VMware واقعی، یک inventory کامل شامل Datacenter، Cluster، Host، VM و Datastore شبیه‌سازی می‌کند.

---

## نصب vcsim

### روش ۱ — از طریق Go

```bash
go install github.com/vmware/govmomi/vcsim@latest
```

### روش ۲ — Docker

```bash
docker run -d --name vcsim \
  -p 8989:8989 \
  vmware/vcsim:latest \
  -httptest.serve 0.0.0.0:8989
```

---

## راه‌اندازی vcsim

```bash
# Inventory پیش‌فرض: 2 DC، 2 Cluster، 4 Host، 20 VM، 4 Datastore
vcsim -httptest.serve 127.0.0.1:8989

# Inventory سفارشی‌تر (پیچیده‌تر برای تست بهتر)
vcsim \
  -dc 2 \
  -cluster 3 \
  -host 5 \
  -vm 30 \
  -pool 2 \
  -ds 6 \
  -httptest.serve 127.0.0.1:8989
```

| Flag | توضیح | پیش‌فرض |
|------|--------|---------|
| `-dc` | تعداد Datacenter | 1 |
| `-cluster` | تعداد Cluster در هر DC | 1 |
| `-host` | تعداد Host در هر Cluster | 2 |
| `-vm` | تعداد VM (توزیع می‌شود) | 2 |
| `-ds` | تعداد Datastore | 1 |
| `-pool` | تعداد Resource Pool | 1 |

اطلاعات اتصال vcsim:
- **Host:** `127.0.0.1:8989`
- **Username:** `user`
- **Password:** `pass`

---

## اجرای تست‌ها

```bash
cd backend

# ۱. vcsim را در یک terminal راه‌اندازی کن
vcsim -dc 2 -cluster 2 -host 4 -vm 20 -ds 4 -httptest.serve 127.0.0.1:8989 &

# ۲. تست‌ها را اجرا کن
pytest tests/vcsim/ -v -s

# با متغیرهای محیطی سفارشی
VCSIM_HOST=127.0.0.1 VCSIM_PORT=8989 pytest tests/vcsim/ -v -s
```

---

## Randomization — چرا و چگونه

هر بار که تست‌های vcsim اجرا می‌شوند، **الگوهای نام VM به صورت تصادفی** انتخاب می‌شوند تا سناریوهای مختلف پوشش داده شود:

```
[vcsim] seed=42731 — patterns: ['WEB VMs', 'DB VMs', 'CACHE VMs']
[vcsim] seed=18205 — patterns: ['APP VMs', 'WORKER VMs']
[vcsim] seed=93014 — patterns: ['API VMs', 'PROXY VMs', 'AUTH VMs', 'DB VMs']
```

اگر یک تست fail شد و می‌خواهی دقیقاً همان seed را reproduce کنی:

```bash
# seed را از خروجی تست کپی کن
PYTHONHASHSEED=42731 pytest tests/vcsim/ -v -s
```

---

## ساختار تست‌ها

```
tests/vcsim/
├── conftest.py          ← fixtures: vcenter_service, inventory, random_patterns, session_seed
└── test_vcsim.py
    ├── TestVcsimConnectivity   ← اتصال و ساختار inventory
    ├── TestDRSWithVcsim        ← تحلیل DRS روی inventory زنده
    └── TestStorageWithVcsim    ← تحلیل Storage روی inventory زنده
```

### TestVcsimConnectivity
اتصال، وجود Cluster/Host/VM/Datastore، و نام‌گذاری صحیح را تأیید می‌کند.

### TestDRSWithVcsim
- تحلیل DRS بدون exception اجرا شود
- تعداد VM در هر Rule هرگز از `host_count - 1` بیشتر نشود (**قانون اصلی compliance**)
- گروه‌های تک‌VM هرگز Rule نگیرند
- تعداد کل Rule ها با جمع نتایج Cluster ها یکسان باشد

### TestStorageWithVcsim
- تحلیل Storage بدون exception اجرا شود
- ISO disk ها Violation ایجاد نکنند
- برای هر Violation حداقل یک Proposal وجود داشته باشد
- VM های Scattered توصیه تجمیع دریافت کنند

---

## استفاده در CI

در CI از همین vcsim استفاده می‌شود — بدون نیاز به vCenter واقعی:

```yaml
# از .github/workflows/ci.yml
- name: Install vcsim
  run: go install github.com/vmware/govmomi/vcsim@latest

- name: Start vcsim
  run: |
    $(go env GOPATH)/bin/vcsim \
      -dc 2 -cluster 2 -host 4 -vm 20 -ds 4 \
      -httptest.serve 127.0.0.1:8989 &
    sleep 3

- name: Run vcsim tests
  run: pytest tests/vcsim/ -v
```

---

## افزودن تست جدید

```python
# tests/vcsim/test_my_feature.py
def test_my_feature(inventory, random_patterns, vcenter_service):
    # inventory: dict با کلیدهای clusters، datastores، datastore_clusters
    # random_patterns: list از pattern های تصادفی
    # vcenter_service: اتصال زنده به vcsim
    clusters = inventory["clusters"]
    assert len(clusters) > 0
```
