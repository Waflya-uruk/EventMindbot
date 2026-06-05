import os
import odoorpc

ODOO_HOST = os.getenv("ODOO_HOST", "eventmind.chilloutnetwork.ru")
ODOO_PORT = int(os.getenv("ODOO_PORT", 443))
ODOO_DB = os.getenv("ODOO_DB", "odoo_db")
ODOO_USER = os.getenv("ODOO_USER", "odoo@ya.ru")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "odoo")

def get_odoo_client() -> odoorpc.ODOO: 
    """Вспомогательная функция для безопасного подключения к Odoo."""
    protocol = "jsonrpc+ssl" if ODOO_PORT == 443 else "jsonrpc"
    odoo = odoorpc.ODOO(
        ODOO_HOST, protocol=protocol, port=ODOO_PORT, timeout=10
    )
    odoo.login(ODOO_DB, ODOO_USER, ODOO_PASSWORD)
    return odoo