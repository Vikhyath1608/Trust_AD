"""
ChromaDB Vector Store Manager
Usage:
  python manage_vectordb.py list                    # list all 416 entries
  python manage_vectordb.py list --filter xpulse    # filter by query text
  python manage_vectordb.py delete 212 214 215      # delete by ID
  python manage_vectordb.py delete --filter "laptop" --product "motorcycle"  # delete wrong classifications
  python manage_vectordb.py stats                   # summary stats
"""
import sqlite3
import argparse
import sys

DB_PATH = "chroma.sqlite3"


def get_conn():
    return sqlite3.connect(DB_PATH)


def fetch_all(conn, filter_text=None, filter_product=None, filter_category=None):
    cur = conn.cursor()
    cur.execute("""
        SELECT e.id,
               MAX(CASE WHEN m.key = 'chroma:document' THEN m.string_value END) as query,
               MAX(CASE WHEN m.key = 'category'        THEN m.string_value END) as category,
               MAX(CASE WHEN m.key = 'product'         THEN m.string_value END) as product,
               MAX(CASE WHEN m.key = 'brand'           THEN m.string_value END) as brand,
               MAX(CASE WHEN m.key = 'is_product'      THEN m.bool_value   END) as is_product
        FROM embeddings e
        JOIN embedding_metadata m ON e.id = m.id
        GROUP BY e.id
        ORDER BY e.id
    """)
    rows = cur.fetchall()
    if filter_text:
        ft = filter_text.lower()
        rows = [r for r in rows if ft in (r[1] or "").lower()]
    if filter_product:
        fp = filter_product.lower()
        rows = [r for r in rows if fp in (r[3] or "").lower()]
    if filter_category:
        fc = filter_category.lower()
        rows = [r for r in rows if fc in (r[2] or "").lower()]
    return rows


def cmd_list(args):
    conn = get_conn()
    rows = fetch_all(conn,
                     filter_text=args.filter,
                     filter_product=getattr(args, 'product', None),
                     filter_category=getattr(args, 'category', None))
    print(f"{'ID':>4}  {'QUERY':<45}  {'CATEGORY':<22}  {'PRODUCT':<18}  BRAND")
    print("-" * 110)
    for r in rows:
        print(f"{r[0]:>4}  {str(r[1])[:44]:<45}  {str(r[2])[:21]:<22}  {str(r[3])[:17]:<18}  {r[4]}")
    print(f"\nTotal: {len(rows)} entries")
    conn.close()


def cmd_delete(args):
    conn = get_conn()

    if hasattr(args, 'ids') and args.ids:
        ids_to_delete = [int(i) for i in args.ids]
    else:
        # Filter-based deletion
        rows = fetch_all(conn,
                         filter_text=getattr(args, 'filter', None),
                         filter_product=getattr(args, 'product', None),
                         filter_category=getattr(args, 'category', None))
        if not rows:
            print("No entries match the filter.")
            return
        print("Entries to delete:")
        for r in rows:
            print(f"  id={r[0]}  query={str(r[1])[:50]}  product={r[3]}")
        confirm = input(f"\nDelete {len(rows)} entries? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("Aborted.")
            return
        ids_to_delete = [r[0] for r in rows]

    cur = conn.cursor()
    deleted = 0
    for eid in ids_to_delete:
        cur.execute("SELECT string_value FROM embedding_metadata WHERE id=? AND key='chroma:document'", (eid,))
        row = cur.fetchone()
        query = row[0] if row else "?"
        cur.execute("DELETE FROM embedding_metadata WHERE id=?", (eid,))
        cur.execute("DELETE FROM embeddings WHERE id=?", (eid,))
        cur.execute("DELETE FROM embedding_fulltext_search WHERE rowid=?", (eid,))
        cur.execute("DELETE FROM embeddings_queue WHERE id=?", (eid,))
        print(f"  Deleted id={eid}: {query}")
        deleted += 1

    conn.commit()
    print(f"\nDeleted {deleted} entries. Remaining: {conn.execute('SELECT COUNT(*) FROM embeddings').fetchone()[0]}")
    conn.close()


def cmd_stats(args):
    conn = get_conn()
    cur = conn.cursor()

    total = cur.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    print(f"Total entries: {total}")

    cur.execute("""
        SELECT MAX(CASE WHEN m.key='category' THEN m.string_value END) as cat, COUNT(*) as cnt
        FROM embeddings e JOIN embedding_metadata m ON e.id=m.id
        GROUP BY e.id
    """)
    from collections import Counter
    cat_counts = Counter()
    for r in cur.fetchall():
        cat_counts[r[0] or "(none)"] += 1
    print("\nBy category:")
    for cat, cnt in sorted(cat_counts.items(), key=lambda x: -x[1]):
        print(f"  {cnt:4d}  {cat}")

    cur.execute("""
        SELECT MAX(CASE WHEN m.key='product' THEN m.string_value END) as prod, COUNT(*) as cnt
        FROM embeddings e JOIN embedding_metadata m ON e.id=m.id
        GROUP BY e.id
        HAVING prod != '' AND prod IS NOT NULL
    """)
    prod_counts = Counter()
    for r in cur.fetchall():
        prod_counts[r[0].lower()] += 1
    print("\nTop 20 products:")
    for prod, cnt in prod_counts.most_common(20):
        print(f"  {cnt:4d}  {prod}")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChromaDB Vector Store Manager")
    sub = parser.add_subparsers(dest="cmd")

    p_list = sub.add_parser("list", help="List entries")
    p_list.add_argument("--filter", help="Filter by query text")
    p_list.add_argument("--product", help="Filter by product")
    p_list.add_argument("--category", help="Filter by category")

    p_del = sub.add_parser("delete", help="Delete entries by ID or filter")
    p_del.add_argument("ids", nargs="*", help="IDs to delete")
    p_del.add_argument("--filter", help="Filter by query text")
    p_del.add_argument("--product", help="Filter by product")
    p_del.add_argument("--category", help="Filter by category")

    p_stats = sub.add_parser("stats", help="Show statistics")

    args = parser.parse_args()
    if args.cmd == "list":   cmd_list(args)
    elif args.cmd == "delete": cmd_delete(args)
    elif args.cmd == "stats":  cmd_stats(args)
    else: parser.print_help()