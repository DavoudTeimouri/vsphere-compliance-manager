"""
Root conftest.py — imports all fixtures from fixtures/ so they're
available to every test file without explicit imports.
"""
from tests.fixtures.vcenter_sim import (  # noqa: F401
    vcenter_sim,
    sim_inventory,
    sim_inventory_clean,
    sim_inventory_small,
    sim_inventory_large,
    default_patterns,
)
