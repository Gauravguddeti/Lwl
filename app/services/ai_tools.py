"""
AI Tools for database access and telecaller functionality
Tools that can be called by the LangGraph AI agent
"""

import json
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from app.database.postgres_data_access import db_access
import logging

logger = logging.getLogger(__name__)

@tool
def get_partners(partner_type: Optional[str] = None) -> str:
    """Get list of partners (schools, institutes, agencies) with optional filtering by type.
    
    Args:
        partner_type: Filter by partner type: 'Institute', 'School', or 'Agency'
    """
    try:
        partners = db_access.get_partners(partner_type)
        return json.dumps({
            "status": "success",
            "data": partners,
            "count": len(partners)
        }, default=str)
    except Exception as e:
        logger.error(f"Error in get_partners tool: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)})

@tool
def get_partner_by_id(partner_id: int) -> str:
    """Get detailed information about a specific partner by their ID.
    
    Args:
        partner_id: ID of the partner to retrieve
    """
    try:
        partner = db_access.get_partner_by_id(partner_id)
        return json.dumps({
            "status": "success",
            "data": partner
        }, default=str)
    except Exception as e:
        logger.error(f"Error in get_partner_by_id tool: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)})

@tool
def get_programs(partner_id: Optional[int] = None) -> str:
    """Get list of educational programs with optional filtering by partner.
    
    Args:
        partner_id: Filter programs by partner ID
    """
    try:
        programs = db_access.get_programs(partner_id)
        return json.dumps({
            "status": "success",
            "data": programs,
            "count": len(programs)
        }, default=str)
    except Exception as e:
        logger.error(f"Error in get_programs tool: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)})

@tool
def get_program_by_id(program_id: int) -> str:
    """Get detailed information about a specific program by its ID.
    
    Args:
        program_id: ID of the program to retrieve
    """
    try:
        program = db_access.get_program_by_id(program_id)
        return json.dumps({
            "status": "success",
            "data": program
        }, default=str)
    except Exception as e:
        logger.error(f"Error in get_program_by_id tool: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)})

@tool
def get_program_events(program_id: Optional[int] = None) -> str:
    """Get list of program events with optional filtering by program.
    
    Args:
        program_id: Filter events by program ID
    """
    try:
        events = db_access.get_program_events(program_id)
        return json.dumps({
            "status": "success",
            "data": events,
            "count": len(events)
        }, default=str)
    except Exception as e:
        logger.error(f"Error in get_program_events tool: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)})

@tool
def get_program_event_by_id(event_id: int) -> str:
    """Get detailed information about a specific program event by its ID.
    
    Args:
        event_id: ID of the program event to retrieve
    """
    try:
        event = db_access.get_program_event_by_id(event_id)
        return json.dumps({
            "status": "success",
            "data": event
        }, default=str)
    except Exception as e:
        logger.error(f"Error in get_program_event_by_id tool: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)})

@tool
def search_programs(search_term: str) -> str:
    """Search for programs by name or partial name match.
    
    Args:
        search_term: Search term for program names
    """
    try:
        programs = db_access.search_programs_by_name(search_term)
        return json.dumps({
            "status": "success",
            "data": programs,
            "count": len(programs),
            "search_term": search_term
        }, default=str)
    except Exception as e:
        logger.error(f"Error in search_programs tool: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)})

@tool
def get_upcoming_events(days_ahead: int = 30) -> str:
    """Get upcoming program events within a specified number of days.
    
    Args:
        days_ahead: Number of days ahead to search for events
    """
    try:
        events = db_access.get_upcoming_events(days_ahead)
        return json.dumps({
            "status": "success",
            "data": events,
            "count": len(events),
            "days_ahead": days_ahead
        }, default=str)
    except Exception as e:
        logger.error(f"Error in get_upcoming_events tool: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)})

@tool
def get_scheduled_job_events(job_id: Optional[int] = None) -> str:
    """Get scheduled job events with complete information about partners, programs, and events.
    
    Args:
        job_id: Filter by scheduled job ID
    """
    try:
        events = db_access.get_scheduled_job_events(job_id)
        return json.dumps({
            "status": "success",
            "data": events,
            "count": len(events)
        }, default=str)
    except Exception as e:
        logger.error(f"Error in get_scheduled_job_events tool: {str(e)}")
        return json.dumps({"status": "error", "message": str(e)})

def get_database_tools() -> List:
    """Get all database tools for LangGraph agent"""
    return [
        get_partners,
        get_partner_by_id,
        get_programs,
        get_program_by_id,
        get_program_events,
        get_program_event_by_id,
        search_programs,
        get_upcoming_events,
        get_scheduled_job_events,
    ]
