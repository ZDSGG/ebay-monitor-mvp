from sqlalchemy import text

from app.core.database import engine
from app.models import Base


def main() -> None:
    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE crawl_jobs ADD COLUMN IF NOT EXISTS shop_id UUID"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_crawl_jobs_shop_id ON crawl_jobs (shop_id)"))
        connection.execute(text("ALTER TABLE shop_listings ADD COLUMN IF NOT EXISTS sales_summary VARCHAR(255)"))
        connection.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM information_schema.table_constraints
                        WHERE constraint_name = 'fk_crawl_jobs_shop_id'
                          AND table_name = 'crawl_jobs'
                    ) THEN
                        ALTER TABLE crawl_jobs
                        ADD CONSTRAINT fk_crawl_jobs_shop_id
                        FOREIGN KEY (shop_id)
                        REFERENCES shops (id)
                        ON DELETE SET NULL;
                    END IF;
                END $$;
                """
            )
        )

    print("V2 shop schema applied.")


if __name__ == "__main__":
    main()
