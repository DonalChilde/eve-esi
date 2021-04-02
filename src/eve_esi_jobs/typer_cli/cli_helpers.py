"""Common helper functions"""
import json
import logging
from pathlib import Path
from typing import Any, Dict

import typer

logger = logging.getLogger(__name__)


def load_json(file_path: Path, **kwargs) -> Any:
    """
    Load a json file.

    :param file_path: :py:class:`pathlib.Path` to the json file.
    :param `**kwargs`: Addtional key word arguments supplied to :func:`json.load()`.
    :raises Exception: Any exception raised during the loading of the file, or the conversion to json.
    :return: The loaded json file.
    """

    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file, **kwargs)
        return data
    except Exception as error:
        logger.exception(
            "Error trying to load json file from %s", file_path, exc_info=True
        )
        raise error


def save_json(
    data: Any,
    file_path: Path,
    mode: str = "w",
    indent: int = 2,
    sort_keys: bool = False,
    parents: bool = False,
    exist_ok: bool = True,
    **kwargs,
):
    """
    Save a json file. Can create parent directories if necessary.

    'w' for writing (truncating the file if it already exists), 'x' for exclusive
    creation.

    :param data: Data to save to json file.
    :param file_path: Output :py:class:`pathlib.Path` to json file.
    :param mode: File mode to use. As used in :func:`open`. Limited to 'w' or 'x'. Defaults to 'w'.
    :param indent: Spaces to indent json output. Defaults to 2.
    :param sort_keys: Sort key of json dicts. Defaults to ``False``.
    :param parents: Make parent directories if they don't exist. As used by :func:`pathlib.Path.mkdir()`. Defaults to ``False``.
    :param exist_ok: Suppress exception if parent directory exists as directory. As used by :func:`pathlib.Path.mkdir`. Defaults to ``True``.
    :param `**kwargs`: Addtional key word arguments supplied to :func:`json.dump()`.
    :raises ValueError: If unsupported file mode is used.
    :raises Exception: Any exception raised during the saving of the file, or the conversion from json.
    """

    kwargs["indent"] = indent
    kwargs["sort_keys"] = sort_keys

    try:
        if mode not in ["w", "x"]:
            raise ValueError(f"Unsupported file mode '{mode}'.")
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=parents, exist_ok=exist_ok)
        with open(file_path, mode) as json_file:
            json.dump(data, json_file, **kwargs)
    except Exception as error:
        logger.exception(
            "Error trying to save json data to %s", file_path, exc_info=True
        )
        raise error


def validate_input_path(path_in: str) -> str:
    """
    Ensure the input path exists, raise an error and exit the script if it does not.

    Args:
        path_in: The path as a string

    Raises:
        typer.BadParameter:

    Returns:
        The path string as a Path.
    """
    input_path: Path = Path(path_in)
    if not input_path.exists():
        raise typer.BadParameter(f"Input path {input_path.resolve()} does not exist.")
    return str(input_path)


def validate_output_path(path_out: str) -> str:
    """
    Checks to see if the path is a file.

    Does not check to see if it is a directory, or if it exists.

    Args:
        path_out: the path as a string.

    Raises:
        typer.BadParameter:

    Returns:
        The path string as a Path
    """
    output_path: Path = Path(path_out)
    if output_path.is_file():
        raise typer.BadParameter(
            f"Output path {output_path.resolve()} is not a directory."
        )
    return str(output_path)


def load_esi_work_order_json(file_path: Path) -> Dict:
    """
    Load a json file. Exit script on error.

    Args:
        file_path: Path to be loaded.

    Raises:
        typer.BadParameter: [description]
        typer.BadParameter: [description]

    Returns:
        The json file.
    """
    try:
        json_data = load_json(file_path)
    except json.decoder.JSONDecodeError as ex:
        raise typer.BadParameter(
            f"Error loading json file at {file_path.resolve()} "
            "are you sure it is a json file?"
        )
    except Exception as ex:
        raise typer.BadParameter(
            f"Error loading json file at {file_path.resolve()}\n"
            f"The error reported was {ex.__class__} with msg {ex}"
        )
    return json_data


def completion_op_id(ctx: typer.Context, incomplete: str):
    completion = []
    for name in OPID:
        if name.startswith(incomplete):
            completion.append(name)
    return completion


def check_for_op_id(ctx: typer.Context, value: str):
    esi_provider = ctx.obj["esi_provider"]
    op_id_keys = list(esi_provider.op_id_lookup.keys())
    if value not in op_id_keys:
        raise typer.BadParameter(f"Only op_ids are allowed, tried: {value}")
    return value


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
