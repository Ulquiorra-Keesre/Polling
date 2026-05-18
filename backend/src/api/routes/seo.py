from fastapi import APIRouter, Response, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.connection import get_db
from src.models.poll import Poll
from datetime import datetime

router = APIRouter(tags=["SEO"])


@router.get("/sitemap.xml", response_class=Response)
async def get_sitemap(db: AsyncSession = Depends(get_db)):

    base_url = "https://index_poll.com"

    static_pages = [
        {
            "loc": f"{base_url}/",
            "lastmod": datetime.utcnow().isoformat(),
            "priority": "1.0",
            "changefreq": "daily",
        },
        {
            "loc": f"{base_url}/dashboard",
            "lastmod": datetime.utcnow().isoformat(),
            "priority": "0.9",
            "changefreq": "daily",
        },
        {
            "loc": f"{base_url}/about",
            "lastmod": datetime.utcnow().isoformat(),
            "priority": "0.5",
            "changefreq": "monthly",
        },
    ]

    result = await db.execute(select(Poll).where(Poll.end_date > datetime.utcnow()))
    active_polls = result.scalars().all()

    poll_pages = [
        {
            "loc": f"{base_url}/poll/{poll.id}",
            "lastmod": poll.created_at.isoformat()
            if poll.created_at
            else datetime.utcnow().isoformat(),
            "priority": "0.8",
            "changefreq": "weekly",
        }
        for poll in active_polls[:100]
    ]

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    for page in static_pages + poll_pages:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{page['loc']}</loc>")
        xml_lines.append(f"    <lastmod>{page['lastmod']}</lastmod>")
        xml_lines.append(f"    <changefreq>{page['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{page['priority']}</priority>")
        xml_lines.append("  </url>")

    xml_lines.append("</urlset>")

    return Response(content="\n".join(xml_lines), media_type="application/xml")


@router.get("/robots.txt", response_class=Response)
async def get_robots():
    content = """User-agent: *
Allow: /
Allow: /about

Disallow: /login
Disallow: /register
Disallow: /admin
Disallow: /profile
Disallow: /api/
Disallow: /results/
Disallow: /dashboard
Disallow: /poll

Disallow: /*?*sort=
Disallow: /*?*page=

Sitemap: https://index_poll.com/sitemap.xml
Host: https://index_poll.com
"""
    return Response(content=content, media_type="text/plain")
