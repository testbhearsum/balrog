from sqlalchemy import Table, Column, Integer, MetaData


metadata = MetaData()

dockerflow = Table("dockerflow", metadata, Column("watchdog", Integer, nullable=False))


def upgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.create_all()


def downgrade(migrate_engine):
    metadata.bind = migrate_engine
    metadata.create_all()
