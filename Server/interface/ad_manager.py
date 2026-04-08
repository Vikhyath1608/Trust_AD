"""
Ad Management Interface — Streamlit App

Upload ads, manage the repository, and view analytics.

Run:
    cd Server
    streamlit run interfaces/ad_manager.py --server.port 8502
"""
import io
import json
import math
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────────────────────────────────────

SERVER_API = "http://localhost:8001"

st.set_page_config(
    page_title="Ad Manager — AdServing Platform",
    page_icon="📢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get(path: str, params: dict = None) -> Optional[Any]:
    try:
        r = requests.get(f"{SERVER_API}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error("❌ Cannot connect to Server API. Is it running on port 8001?")
        return None
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def _post(path: str, data: dict) -> Optional[Any]:
    try:
        r = requests.post(f"{SERVER_API}{path}", json=data, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        st.error(f"API error {e.response.status_code}: {e.response.text[:300]}")
        return None
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def _patch(path: str, data: dict) -> Optional[Any]:
    try:
        r = requests.patch(f"{SERVER_API}{path}", json=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Update failed: {e}")
        return None


def _delete(path: str) -> bool:
    try:
        r = requests.delete(f"{SERVER_API}{path}", timeout=10)
        return r.status_code == 204
    except Exception as e:
        st.error(f"Delete failed: {e}")
        return False


def _upload_image(file_obj) -> Optional[str]:
    try:
        r = requests.post(
            f"{SERVER_API}/ads/upload-image",
            files={"file": (file_obj.name, file_obj.getvalue(), file_obj.type)},
            timeout=20,
        )
        r.raise_for_status()
        return r.json().get("image_url")
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None


def _metric_row(cols, labels_values: list):
    for col, (label, value) in zip(cols, labels_values):
        col.metric(label, value)


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/color/96/advertisement.png", width=64)
    st.title("Ad Manager")
    st.caption("AdServing Platform — Management Console")
    st.divider()

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "➕ Upload Ad", "📋 Manage Ads", "📈 Analytics"],
        label_visibility="collapsed",
    )

    st.divider()

    health = _get("/health")
    if health:
        status_emoji = "🟢" if health.get("status") == "healthy" else "🔴"
        st.caption(f"{status_emoji} Server: **{health.get('status', 'unknown')}**")
        st.caption(f"🗄️ DB: `{health.get('database', '?')}`")
    else:
        st.caption("🔴 Server unreachable")

# ─────────────────────────────────────────────────────────────────────────────
# Page: Dashboard
# ─────────────────────────────────────────────────────────────────────────────

if page == "📊 Dashboard":
    st.title("📊 Platform Dashboard")

    data = _get("/analytics/overview")
    if not data:
        st.stop()

    # ── KPIs ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Ads", data["total_ads"])
    c2.metric("Active Ads", data["active_ads"])
    c3.metric("Inactive Ads", data["inactive_ads"])
    c4.metric("Total Impressions", f"{data['total_impressions']:,}")
    c5.metric("Overall CTR", f"{data['overall_ctr']*100:.2f}%")

    st.divider()

    col_left, col_right = st.columns(2)

    # ── Top categories ─────────────────────────────────────────────────────
    with col_left:
        st.subheader("📂 Top Categories by Impressions")
        cats = data.get("top_categories", [])
        if cats:
            df_cats = pd.DataFrame(cats)[
                ["category", "ad_count", "total_impressions", "total_clicks", "avg_ctr"]
            ]
            df_cats["avg_ctr"] = (df_cats["avg_ctr"] * 100).round(2).astype(str) + "%"
            df_cats.columns = ["Category", "Ads", "Impressions", "Clicks", "Avg CTR"]
            st.dataframe(df_cats, use_container_width=True, hide_index=True)

            # Bar chart
            st.bar_chart(
                pd.DataFrame(cats).set_index("category")["total_impressions"],
                color="#6366f1",
            )
        else:
            st.info("No impression data yet.")

    # ── Top ads by impressions ─────────────────────────────────────────────
    with col_right:
        st.subheader("🏆 Top Ads by Impressions")
        top_imp = data.get("top_ads_by_impressions", [])
        if top_imp:
            df_top = pd.DataFrame(top_imp)[
                ["ad_id", "title", "category", "impression_count", "ctr"]
            ]
            df_top["ctr"] = (df_top["ctr"] * 100).round(2).astype(str) + "%"
            df_top.columns = ["ID", "Title", "Category", "Impressions", "CTR"]
            df_top["Title"] = df_top["Title"].str[:45]
            st.dataframe(df_top, use_container_width=True, hide_index=True)
        else:
            st.info("No impression data yet.")

    # ── Keyword distribution ───────────────────────────────────────────────
    st.subheader("🔑 Keyword Distribution")
    kw_data = _get("/analytics/keywords", {"limit": 15})
    if kw_data and kw_data.get("keywords"):
        kw_series = pd.Series(kw_data["keywords"])
        st.bar_chart(kw_series, color="#10b981")
    else:
        st.info("No keyword data yet.")

# ─────────────────────────────────────────────────────────────────────────────
# Page: Upload Ad
# ─────────────────────────────────────────────────────────────────────────────

elif page == "➕ Upload Ad":
    st.title("➕ Upload New Ad")
    st.caption("Fill in the creative details and targeting parameters.")

    with st.form("create_ad_form", clear_on_submit=True):
        st.subheader("Creative Content")
        col1, col2 = st.columns([2, 1])
        with col1:
            title = st.text_input("Ad Title *", placeholder="Samsung Galaxy S24 — Best Price")
            description = st.text_area(
                "Ad Description *",
                placeholder="Compelling ad copy that drives clicks...",
                height=100,
            )
            destination_url = st.text_input(
                "Click-Through URL",
                placeholder="https://yoursite.com/product",
            )
        with col2:
            uploaded_file = st.file_uploader(
                "Creative Image",
                type=["jpg", "jpeg", "png", "webp", "gif"],
                help="Max 10MB. JPEG, PNG, WebP, or GIF.",
            )
            if uploaded_file:
                st.image(uploaded_file, use_container_width=True)

        st.subheader("Targeting")
        col3, col4 = st.columns(2)
        with col3:
            category = st.selectbox(
                "Category *",
                [
                    "Electronics", "Fashion", "Home Appliances", "Automotive",
                    "Health & Fitness", "Food & Grocery", "Travel", "Education",
                    "Beauty & Personal Care", "Sports & Outdoors", "Books",
                    "Toys & Games", "Finance", "Real Estate", "Other",
                ],
            )
            brand = st.text_input("Brand", placeholder="Samsung, Nike, Apple...")
        with col4:
            keywords_raw = st.text_area(
                "Targeting Keywords (one per line, max 20)",
                placeholder="samsung\ngalaxy\nsmartphone\nandroid",
                height=120,
                help="Keywords matched against user interest signals.",
            )

        st.subheader("Budget & Bidding")
        col5, col6, col7 = st.columns(3)
        with col5:
            budget = st.number_input("Total Budget (USD)", min_value=0.0, value=1000.0, step=100.0)
        with col6:
            bid_cpm = st.number_input("Bid CPM (USD)", min_value=0.0, value=2.0, step=0.5,
                                       help="Cost per 1000 impressions")
        with col7:
            is_active = st.checkbox("Launch as Active", value=True)

        submitted = st.form_submit_button("🚀 Create Ad", use_container_width=True, type="primary")

    if submitted:
        # Validate required fields
        errors = []
        if not title.strip():
            errors.append("Ad Title is required.")
        if not description.strip():
            errors.append("Ad Description is required.")

        if errors:
            for e in errors:
                st.error(e)
        else:
            # Upload image if provided
            image_url = None
            if uploaded_file:
                with st.spinner("Uploading image..."):
                    image_url = _upload_image(uploaded_file)
                if image_url:
                    st.success(f"✓ Image uploaded: `{image_url}`")

            # Parse keywords
            keywords = [
                kw.strip().lower()
                for kw in keywords_raw.split("\n")
                if kw.strip()
            ][:20]

            payload = {
                "title": title.strip(),
                "description": description.strip(),
                "image_url": image_url,
                "destination_url": destination_url.strip() or None,
                "category": category,
                "brand": brand.strip() or None,
                "keywords": keywords,
                "budget": budget,
                "bid_cpm": bid_cpm,
                "is_active": is_active,
            }

            with st.spinner("Creating ad..."):
                result = _post("/ads/", payload)

            if result:
                st.success(f"✅ Ad created successfully! **ID: {result['id']}**")
                with st.expander("View created ad"):
                    st.json(result)

# ─────────────────────────────────────────────────────────────────────────────
# Page: Manage Ads
# ─────────────────────────────────────────────────────────────────────────────

elif page == "📋 Manage Ads":
    st.title("📋 Ad Repository")

    # ── Filters ───────────────────────────────────────────────────────────
    col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 1])
    with col_f1:
        filter_active = st.selectbox("Status", ["All", "Active Only", "Inactive Only"])
    with col_f2:
        filter_category = st.text_input("Category contains", "")
    with col_f3:
        page_num = st.number_input("Page", min_value=1, value=1)
    with col_f4:
        page_size = st.selectbox("Per page", [10, 20, 50], index=1)

    params: dict = {"page": page_num, "page_size": page_size}
    if filter_active == "Active Only":
        params["active_only"] = "true"
    elif filter_active == "Inactive Only":
        params["active_only"] = "false"
    if filter_category:
        params["category"] = filter_category

    data = _get("/ads/", params)
    if not data:
        st.stop()

    total = data["total"]
    ads_list = data["items"]

    st.caption(f"Showing {len(ads_list)} of {total} ads — Page {page_num} of {data['total_pages']}")
    st.divider()

    if not ads_list:
        st.info("No ads found. Upload some ads first.")
        st.stop()

    # ── Ad cards ──────────────────────────────────────────────────────────
    for ad in ads_list:
        status_badge = "🟢 Active" if ad["is_active"] else "🔴 Inactive"
        imp = ad.get("impression_count", 0) or 0
        clk = ad.get("click_count", 0) or 0
        ctr = (ad.get("ctr") or 0) * 100

        with st.expander(
            f"**#{ad['id']}** — {ad['title'][:60]}  |  {ad['category']}  |  {status_badge}  |  "
            f"👁 {imp} imps  |  🖱 {clk} clicks  |  CTR {ctr:.2f}%"
        ):
            col_info, col_actions = st.columns([3, 1])

            with col_info:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Title:** {ad['title']}")
                    st.markdown(f"**Category:** {ad['category']}")
                    st.markdown(f"**Brand:** {ad.get('brand') or '—'}")
                    st.markdown(f"**Budget:** ${ad['budget']:,.2f}  |  **CPM:** ${ad['bid_cpm']:.2f}")
                with c2:
                    st.markdown(f"**Description:**")
                    st.caption(ad["description"][:200])
                    kws = ad.get("keywords", [])
                    if kws:
                        st.markdown("**Keywords:** " + "  ".join([f"`{k}`" for k in kws]))
                    if ad.get("destination_url"):
                        st.markdown(f"**URL:** `{ad['destination_url'][:60]}`")

                if ad.get("image_url"):
                    st.image(f"{SERVER_API}{ad['image_url']}", width=200)

            with col_actions:
                st.markdown("**Actions**")

                # Toggle active
                toggle_label = "⏸ Deactivate" if ad["is_active"] else "▶ Activate"
                if st.button(toggle_label, key=f"toggle_{ad['id']}", use_container_width=True):
                    result = _patch(f"/ads/{ad['id']}/toggle", {})
                    if result:
                        new_status = "Active" if result["is_active"] else "Inactive"
                        st.success(f"Status → {new_status}")
                        st.rerun()

                # Edit (inline keywords update)
                with st.popover("✏️ Edit Keywords", use_container_width=True):
                    new_kws = st.text_area(
                        "Keywords (one per line)",
                        value="\n".join(ad.get("keywords", [])),
                        key=f"kw_edit_{ad['id']}",
                        height=100,
                    )
                    if st.button("Save", key=f"save_kw_{ad['id']}"):
                        kw_list = [k.strip().lower() for k in new_kws.split("\n") if k.strip()]
                        result = _patch(f"/ads/{ad['id']}", {"keywords": kw_list})
                        if result:
                            st.success("Keywords updated!")
                            st.rerun()

                # Delete
                if st.button("🗑 Delete", key=f"del_{ad['id']}", use_container_width=True, type="secondary"):
                    if _delete(f"/ads/{ad['id']}"):
                        st.success("Deleted.")
                        st.rerun()
                    else:
                        st.error("Delete failed.")

# ─────────────────────────────────────────────────────────────────────────────
# Page: Analytics
# ─────────────────────────────────────────────────────────────────────────────

elif page == "📈 Analytics":
    st.title("📈 Ad Analytics")

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("Per-Ad Lookup")
        ad_id_input = st.number_input("Ad ID", min_value=1, step=1)
        if st.button("🔍 Get Analytics", use_container_width=True):
            ad_data = _get(f"/analytics/ads/{ad_id_input}")
            if ad_data:
                ctr_pct = ad_data.get("ctr", 0) * 100
                m1, m2, m3 = st.columns(3)
                m1.metric("Impressions", ad_data.get("impression_count", 0))
                m2.metric("Clicks", ad_data.get("click_count", 0))
                m3.metric("CTR", f"{ctr_pct:.2f}%")
                st.markdown(f"**{ad_data['title']}**")
                st.caption(f"Category: {ad_data['category']}  |  Brand: {ad_data.get('brand') or '—'}")
                st.caption(f"Budget: ${ad_data['budget']:,.2f}  |  CPM: ${ad_data['bid_cpm']:.2f}")

    with col_right:
        st.subheader("Impressions Over Time")
        time_ad_filter = st.number_input(
            "Filter by Ad ID (0 = all)", min_value=0, value=0, step=1
        )
        params = {}
        if time_ad_filter > 0:
            params["ad_id"] = time_ad_filter

        ts_data = _get("/analytics/impressions/time", params)
        if ts_data and ts_data.get("series"):
            df_ts = pd.DataFrame(ts_data["series"])
            df_ts["day"] = pd.to_datetime(df_ts["day"])
            df_ts = df_ts.set_index("day")
            st.line_chart(df_ts["impressions"], color="#6366f1")
        else:
            st.info("No impression time-series data yet.")

    # ── Top ads by CTR ─────────────────────────────────────────────────────
    st.subheader("Top Ads by CTR (min. 5 impressions)")
    overview = _get("/analytics/overview")
    if overview:
        top_ctr = overview.get("top_ads_by_ctr", [])
        if top_ctr:
            df_ctr = pd.DataFrame(top_ctr)[
                ["ad_id", "title", "category", "impression_count", "click_count", "ctr", "budget"]
            ]
            df_ctr["ctr"] = (df_ctr["ctr"] * 100).round(3).astype(str) + "%"
            df_ctr["title"] = df_ctr["title"].str[:50]
            df_ctr.columns = ["ID", "Title", "Category", "Impressions", "Clicks", "CTR", "Budget"]
            st.dataframe(df_ctr, use_container_width=True, hide_index=True)
        else:
            st.info("Need at least 5 impressions per ad for CTR ranking.")