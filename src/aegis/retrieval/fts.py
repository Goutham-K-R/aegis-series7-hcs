import logging
from sqlalchemy import text
from aegis.storage.orm import ExtractionResultORM

logger = logging.getLogger("aegis_fts")

class FTSIndex:
    def __init__(self, session):
        self.session = session
        self._ensure_index()

    def _ensure_index(self):
        # Create virtual table for FTS5
        conn = self.session.connection()
        conn.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS fts_evidence USING fts5(extraction_id UNINDEXED, text)"))
        
        # Check if empty, populate if so
        count = conn.execute(text("SELECT count(*) FROM fts_evidence")).scalar()
        if count == 0:
            logger.info("Populating FTS index...")
            extractions = self.session.query(ExtractionResultORM).all()
            for ext in extractions:
                if ext.raw_text:
                    conn.execute(
                        text("INSERT INTO fts_evidence (extraction_id, text) VALUES (:id, :txt)"),
                        {"id": str(ext.id), "txt": ext.raw_text}
                    )
            self.session.commit()

    def search(self, query: str, limit: int = 10):
        # Very basic lexical match
        conn = self.session.connection()
        import re
        safe_query = re.sub(r'[^\w\s]', '', query)
        # Build FTS syntax (ORed tokens)
        tokens = [t for t in safe_query.split() if len(t) > 2]
        if not tokens:
            return []
        
        fts_query = " OR ".join(tokens)
        
        sql = text("SELECT extraction_id FROM fts_evidence WHERE text MATCH :q ORDER BY rank LIMIT :limit")
        try:
            results = conn.execute(sql, {"q": fts_query, "limit": limit}).fetchall()
            return [r[0] for r in results]
        except Exception as e:
            logger.warning(f"FTS search failed for query '{query}': {e}")
            return []
