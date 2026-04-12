#!/bin/bash
# ============================================================
# EduPath — Tezkor ishga tushirish skripti
# Ishlatish: bash setup.sh
# ============================================================
set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}"
echo "  ███████╗██████╗ ██╗   ██╗██████╗  █████╗ ████████╗██╗  ██╗"
echo "  ██╔════╝██╔══██╗██║   ██║██╔══██╗██╔══██╗╚══██╔══╝██║  ██║"
echo "  █████╗  ██║  ██║██║   ██║██████╔╝███████║   ██║   ███████║"
echo "  ██╔══╝  ██║  ██║██║   ██║██╔═══╝ ██╔══██║   ██║   ██╔══██║"
echo "  ███████╗██████╔╝╚██████╔╝██║     ██║  ██║   ██║   ██║  ██║"
echo "  ╚══════╝╚═════╝  ╚═════╝ ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚═╝  ╚═╝"
echo -e "${NC}"
echo "  Abituriyentlar uchun AI Platform"
echo ""

# ---- 1. Python tekshirish ----
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 topilmadi. Iltimos o'rnating."
    exit 1
fi
PYTHON_VER=$(python3 -c 'import sys; print(sys.version_info >= (3,10))')
if [ "$PYTHON_VER" != "True" ]; then
    echo "⚠️  Python 3.10+ tavsiya etiladi"
fi

# ---- 2. Virtual muhit ----
if [ ! -d "venv" ]; then
    echo -e "${BLUE}📦 Virtual muhit yaratilmoqda...${NC}"
    python3 -m venv venv
fi
source venv/bin/activate
echo -e "${GREEN}✓ Virtual muhit faol${NC}"

# ---- 3. pip yangilash ----
pip install --upgrade pip -q

# ---- 4. Paketlar ----
echo -e "${BLUE}📥 Paketlar o'rnatilmoqda...${NC}"
pip install -r requirements.txt -q
echo -e "${GREEN}✓ Paketlar o'rnatildi${NC}"

# ---- 5. .env ----
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚙️  .env fayl yaratildi — tahrirlang:${NC}"
    echo "   nano .env"
    echo ""
    echo "   Majburiy: SECRET_KEY, DB sozlamalari"
    echo "   Ixtiyoriy: AI API key (keyinroq admin panelda ham kiritsa bo'ladi)"
    echo ""
fi

# ---- 6. Media papka ----
mkdir -p media staticfiles

# ---- 7. Qaysi DB ishlatish ----
echo ""
echo "Qaysi ma'lumotlar bazasidan foydalanasiz?"
echo "  1) SQLite (tez sinab ko'rish — PostgreSQL shart emas)"
echo "  2) PostgreSQL (.env dagi sozlamalar ishlatiladi)"
read -p "Tanlov [1/2, default: 1]: " DB_CHOICE
DB_CHOICE=${DB_CHOICE:-1}

if [ "$DB_CHOICE" = "1" ]; then
    export USE_SQLITE=True
    echo -e "${GREEN}✓ SQLite tanlandi${NC}"
else
    export USE_SQLITE=False
    echo -e "${GREEN}✓ PostgreSQL tanlandi${NC}"
fi

# ---- 8. Migratsiya ----
echo -e "${BLUE}🗄️  Migratsiyalar bajarilmoqda...${NC}"
USE_SQLITE=$USE_SQLITE python manage.py migrate
echo -e "${GREEN}✓ Ma'lumotlar bazasi tayyor${NC}"

# ---- 9. Static fayllar ----
echo -e "${BLUE}📂 Static fayllar to'planmoqda...${NC}"
USE_SQLITE=$USE_SQLITE python manage.py collectstatic --noinput -v 0
echo -e "${GREEN}✓ Static fayllar tayyor${NC}"

# ---- 10. Superuser ----
echo ""
echo -e "${BLUE}👤 Admin foydalanuvchi yarating:${NC}"
USE_SQLITE=$USE_SQLITE python manage.py createsuperuser

# ---- 11. Demo ma'lumotlar (ixtiyoriy) ----
echo ""
read -p "Demo universitetlar kiritilsinmi? [y/N]: " DEMO
if [ "$DEMO" = "y" ] || [ "$DEMO" = "Y" ]; then
    USE_SQLITE=$USE_SQLITE python manage.py shell << 'PYSHELL'
from universities.models import University
unis = [
    dict(name="O'zbekiston Milliy Universiteti", slug="nuu", country="O'zbekiston", city="Toshkent",
         is_local=True, has_grant=True, ranking=None, min_dtm_score=160,
         grant_description="Davlat granti asosida qabul", is_published=True),
    dict(name="Toshkent Davlat Texnika Universiteti", slug="tdtu", country="O'zbekiston", city="Toshkent",
         is_local=True, has_grant=True, min_dtm_score=150, is_published=True),
    dict(name="INHA University in Tashkent", slug="inha", country="O'zbekiston", city="Toshkent",
         is_local=True, has_grant=False, min_ielts_score=5.5, is_published=True),
    dict(name="Seoul National University", slug="snu", country="Koreya", city="Seul",
         is_local=False, has_grant=True, ranking=36, min_ielts_score=6.5,
         grant_description="GKS scholarship - to'liq grant", is_published=True),
    dict(name="Nazarbayev University", slug="nu-kz", country="Qozog'iston", city="Astana",
         is_local=False, has_grant=True, ranking=None, min_ielts_score=6.0,
         grant_description="Prezident stipendiyasi", is_published=True),
    dict(name="University of Westminster Tashkent", slug="uwt", country="O'zbekiston", city="Toshkent",
         is_local=True, has_grant=False, min_ielts_score=6.0, is_published=True),
]
for u in unis:
    University.objects.get_or_create(slug=u.pop('slug'), defaults=u)
print(f"  {len(unis)} ta demo universitet kiritildi")
PYSHELL
fi

# ---- Done ----
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║   ✅  EduPath ishga tayyor!               ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo "  Ishga tushirish:"
echo -e "  ${BLUE}source venv/bin/activate${NC}"
echo -e "  ${BLUE}USE_SQLITE=True python manage.py runserver${NC}"
echo ""
echo "  🌐 Sayt:   http://127.0.0.1:8000"
echo "  ⚙️  Admin:  http://127.0.0.1:8000/admin/"
echo ""
echo "  Admin panelda:"
echo "  1. SiteSettings → Logo, Favicon, Email sozlang"
echo "  2. AISettings   → Provider va API key kiriting"
echo ""
