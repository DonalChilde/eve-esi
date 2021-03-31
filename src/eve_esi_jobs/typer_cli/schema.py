"""Working with ESI schema"""

import dataclasses
import json
import logging
from pathlib import Path
from time import perf_counter_ns
from typing import Dict, List, Optional

import typer
from pfmsoft.aiohttp_queue import ActionCallbacks, AiohttpAction
from pfmsoft.aiohttp_queue.callbacks import ResponseContentToJson
from pfmsoft.aiohttp_queue.runners import do_action_runner
from rich import inspect

from eve_esi_jobs.esi_provider import EsiProvider
from eve_esi_jobs.typer_cli.app_config import EveEsiJobConfig

# from eve_esi_jobs.app_config import SCHEMA_URL
from eve_esi_jobs.typer_cli.app_data import save_json_to_app_data
from eve_esi_jobs.typer_cli.cli_helpers import save_json

logger = logging.getLogger(__name__)
app = typer.Typer(
    help="Download and inspect Esi schemas. use --help on the commands below for more options."
)


def complete_op_id_3(ctx: typer.Context, incomplete: str):
    completion = []
    for name in OPID:
        if name.startswith(incomplete):
            completion.append(name)
    return completion


def complete_op_id_2(ctx: typer.Context):

    return OPID


def check_for_op_id(ctx: typer.Context, value: str):
    esi_provider = ctx.obj["esi_provider"]
    op_id_keys = list(esi_provider.op_id_lookup.keys())
    if value not in op_id_keys:
        raise typer.BadParameter(f"Only op_ids are allowed, tried: {value}")
    return value


@app.command()
def browse(
    ctx: typer.Context,
    op_id: str = typer.Argument(
        ..., autocompletion=complete_op_id_3, callback=check_for_op_id
    ),
):
    """Browse schema by op_id, use tab for completion."""
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    op_id_info = esi_provider.op_id_lookup.get(op_id, None)
    if op_id_info is None:
        typer.BadParameter(f"Invalid op_id: {op_id}")
    typer.echo(json.dumps(dataclasses.asdict(op_id_info), indent=2))


@app.command()
def list_op_ids(ctx: typer.Context, switch: str = typer.Argument("all")):
    """List available op_ids"""
    esi_provider: EsiProvider = ctx.obj["esi_provider"]
    op_id_keys = list(esi_provider.op_id_lookup)
    op_id_keys.sort()
    if switch == "json":
        op_ids = json.dumps(op_id_keys, indent=2)
    else:
        op_ids = "\n".join(op_id_keys)
    typer.echo(op_ids)


@app.command()
def download(
    ctx: typer.Context,
    url: str = typer.Option(
        "https://esi.evetech.net/latest/swagger.json",
        "--url",
        help="The url to ESI schema.",
    ),
    destination: str = typer.Option(
        "app-data",
        "-d",
        help=(
            "Location to output schema. Use stdout to print to console, "
            "and a file path to save to file."
        ),
    ),
):
    """Download a schema, use --help for more options."""
    config: EveEsiJobConfig = ctx.obj["config"]
    url = config.schema_url
    schema: Optional[Dict] = download_json(url)
    if schema is None:
        typer.BadParameter(f"Unable to download schema from {url}")
    if destination == "app-data":
        version = schema["info"]["version"]
        params = {"version": version}
        file_path = save_json_to_app_data(schema, config.app_dir, "schema", params)
        typer.echo(f"Schema saved to {file_path}")
        typer.Exit()
    elif destination == "stdout":
        typer.echo(json.dumps(schema, indent=2))
        typer.Exit()
    else:
        schema_path = Path(destination) / Path("esi_schema.json")
        save_json(schema, schema_path, parents=True)
        typer.echo(f"Schema saved to {schema_path.resolve()}")
    start = ctx.obj.get("start_time", perf_counter_ns())
    end = perf_counter_ns()
    seconds = (end - start) / 1000000000
    typer.echo(f"Task completed in {seconds:0.2f} seconds")
    # logger.info(
    #     "%s Actions sequentially completed -  took %s seconds, %s actions per second.",
    #     len(actions),
    #     f"{seconds:9f}",
    #     f"{len(actions)/seconds:1f}",
    # )


def download_json(url):
    """Convenience method for downloading a single url, expecting json"""
    callbacks = ActionCallbacks(success=[ResponseContentToJson()])
    action = AiohttpAction("get", url, callbacks=callbacks)
    do_action_runner([action])
    if action.response.status == 200:
        return action.result
    logger.warning(
        "Failed to download url. url: %s, status: %s, msg: %s",
        action.response.real_url,
        action.response.status,
        action.result,
    )
    return None


OPID = [
    "delete_characters_character_id_contacts",
    "delete_characters_character_id_fittings_fitting_id",
    "delete_characters_character_id_mail_labels_label_id",
    "delete_characters_character_id_mail_mail_id",
    "delete_fleets_fleet_id_members_member_id",
    "delete_fleets_fleet_id_squads_squad_id",
    "delete_fleets_fleet_id_wings_wing_id",
    "get_alliances",
    "get_alliances_alliance_id",
    "get_alliances_alliance_id_contacts",
    "get_alliances_alliance_id_contacts_labels",
    "get_alliances_alliance_id_corporations",
    "get_alliances_alliance_id_icons",
    "get_characters_character_id",
    "get_characters_character_id_agents_research",
    "get_characters_character_id_assets",
    "get_characters_character_id_attributes",
    "get_characters_character_id_blueprints",
    "get_characters_character_id_bookmarks",
    "get_characters_character_id_bookmarks_folders",
    "get_characters_character_id_calendar",
    "get_characters_character_id_calendar_event_id",
    "get_characters_character_id_calendar_event_id_attendees",
    "get_characters_character_id_clones",
    "get_characters_character_id_contacts",
    "get_characters_character_id_contacts_labels",
    "get_characters_character_id_contracts",
    "get_characters_character_id_contracts_contract_id_bids",
    "get_characters_character_id_contracts_contract_id_items",
    "get_characters_character_id_corporationhistory",
    "get_characters_character_id_fatigue",
    "get_characters_character_id_fittings",
    "get_characters_character_id_fleet",
    "get_characters_character_id_fw_stats",
    "get_characters_character_id_implants",
    "get_characters_character_id_industry_jobs",
    "get_characters_character_id_killmails_recent",
    "get_characters_character_id_location",
    "get_characters_character_id_loyalty_points",
    "get_characters_character_id_mail",
    "get_characters_character_id_mail_labels",
    "get_characters_character_id_mail_lists",
    "get_characters_character_id_mail_mail_id",
    "get_characters_character_id_medals",
    "get_characters_character_id_mining",
    "get_characters_character_id_notifications",
    "get_characters_character_id_notifications_contacts",
    "get_characters_character_id_online",
    "get_characters_character_id_opportunities",
    "get_characters_character_id_orders",
    "get_characters_character_id_orders_history",
    "get_characters_character_id_planets",
    "get_characters_character_id_planets_planet_id",
    "get_characters_character_id_portrait",
    "get_characters_character_id_roles",
    "get_characters_character_id_search",
    "get_characters_character_id_ship",
    "get_characters_character_id_skillqueue",
    "get_characters_character_id_skills",
    "get_characters_character_id_standings",
    "get_characters_character_id_titles",
    "get_characters_character_id_wallet",
    "get_characters_character_id_wallet_journal",
    "get_characters_character_id_wallet_transactions",
    "get_contracts_public_bids_contract_id",
    "get_contracts_public_items_contract_id",
    "get_contracts_public_region_id",
    "get_corporation_corporation_id_mining_extractions",
    "get_corporation_corporation_id_mining_observers",
    "get_corporation_corporation_id_mining_observers_observer_id",
    "get_corporations_corporation_id",
    "get_corporations_corporation_id_alliancehistory",
    "get_corporations_corporation_id_assets",
    "get_corporations_corporation_id_blueprints",
    "get_corporations_corporation_id_bookmarks",
    "get_corporations_corporation_id_bookmarks_folders",
    "get_corporations_corporation_id_contacts",
    "get_corporations_corporation_id_contacts_labels",
    "get_corporations_corporation_id_containers_logs",
    "get_corporations_corporation_id_contracts",
    "get_corporations_corporation_id_contracts_contract_id_bids",
    "get_corporations_corporation_id_contracts_contract_id_items",
    "get_corporations_corporation_id_customs_offices",
    "get_corporations_corporation_id_divisions",
    "get_corporations_corporation_id_facilities",
    "get_corporations_corporation_id_fw_stats",
    "get_corporations_corporation_id_icons",
    "get_corporations_corporation_id_industry_jobs",
    "get_corporations_corporation_id_killmails_recent",
    "get_corporations_corporation_id_medals",
    "get_corporations_corporation_id_medals_issued",
    "get_corporations_corporation_id_members",
    "get_corporations_corporation_id_members_limit",
    "get_corporations_corporation_id_members_titles",
    "get_corporations_corporation_id_membertracking",
    "get_corporations_corporation_id_orders",
    "get_corporations_corporation_id_orders_history",
    "get_corporations_corporation_id_roles",
    "get_corporations_corporation_id_roles_history",
    "get_corporations_corporation_id_shareholders",
    "get_corporations_corporation_id_standings",
    "get_corporations_corporation_id_starbases",
    "get_corporations_corporation_id_starbases_starbase_id",
    "get_corporations_corporation_id_structures",
    "get_corporations_corporation_id_titles",
    "get_corporations_corporation_id_wallets",
    "get_corporations_corporation_id_wallets_division_journal",
    "get_corporations_corporation_id_wallets_division_transactions",
    "get_corporations_npccorps",
    "get_dogma_attributes",
    "get_dogma_attributes_attribute_id",
    "get_dogma_dynamic_items_type_id_item_id",
    "get_dogma_effects",
    "get_dogma_effects_effect_id",
    "get_fleets_fleet_id",
    "get_fleets_fleet_id_members",
    "get_fleets_fleet_id_wings",
    "get_fw_leaderboards",
    "get_fw_leaderboards_characters",
    "get_fw_leaderboards_corporations",
    "get_fw_stats",
    "get_fw_systems",
    "get_fw_wars",
    "get_incursions",
    "get_industry_facilities",
    "get_industry_systems",
    "get_insurance_prices",
    "get_killmails_killmail_id_killmail_hash",
    "get_loyalty_stores_corporation_id_offers",
    "get_markets_groups",
    "get_markets_groups_market_group_id",
    "get_markets_prices",
    "get_markets_region_id_history",
    "get_markets_region_id_orders",
    "get_markets_region_id_types",
    "get_markets_structures_structure_id",
    "get_opportunities_groups",
    "get_opportunities_groups_group_id",
    "get_opportunities_tasks",
    "get_opportunities_tasks_task_id",
    "get_route_origin_destination",
    "get_search",
    "get_sovereignty_campaigns",
    "get_sovereignty_map",
    "get_sovereignty_structures",
    "get_status",
    "get_universe_ancestries",
    "get_universe_asteroid_belts_asteroid_belt_id",
    "get_universe_bloodlines",
    "get_universe_categories",
    "get_universe_categories_category_id",
    "get_universe_constellations",
    "get_universe_constellations_constellation_id",
    "get_universe_factions",
    "get_universe_graphics",
    "get_universe_graphics_graphic_id",
    "get_universe_groups",
    "get_universe_groups_group_id",
    "get_universe_moons_moon_id",
    "get_universe_planets_planet_id",
    "get_universe_races",
    "get_universe_regions",
    "get_universe_regions_region_id",
    "get_universe_schematics_schematic_id",
    "get_universe_stargates_stargate_id",
    "get_universe_stars_star_id",
    "get_universe_stations_station_id",
    "get_universe_structures",
    "get_universe_structures_structure_id",
    "get_universe_system_jumps",
    "get_universe_system_kills",
    "get_universe_systems",
    "get_universe_systems_system_id",
    "get_universe_types",
    "get_universe_types_type_id",
    "get_wars",
    "get_wars_war_id",
    "get_wars_war_id_killmails",
    "post_characters_affiliation",
    "post_characters_character_id_assets_locations",
    "post_characters_character_id_assets_names",
    "post_characters_character_id_contacts",
    "post_characters_character_id_cspa",
    "post_characters_character_id_fittings",
    "post_characters_character_id_mail",
    "post_characters_character_id_mail_labels",
    "post_corporations_corporation_id_assets_locations",
    "post_corporations_corporation_id_assets_names",
    "post_fleets_fleet_id_members",
    "post_fleets_fleet_id_wings",
    "post_fleets_fleet_id_wings_wing_id_squads",
    "post_ui_autopilot_waypoint",
    "post_ui_openwindow_contract",
    "post_ui_openwindow_information",
    "post_ui_openwindow_marketdetails",
    "post_ui_openwindow_newmail",
    "post_universe_ids",
    "post_universe_names",
    "put_characters_character_id_calendar_event_id",
    "put_characters_character_id_contacts",
    "put_characters_character_id_mail_mail_id",
    "put_fleets_fleet_id",
    "put_fleets_fleet_id_members_member_id",
    "put_fleets_fleet_id_squads_squad_id",
    "put_fleets_fleet_id_wings_wing_id",
]
