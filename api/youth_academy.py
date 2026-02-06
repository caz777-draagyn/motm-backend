"""
API endpoints for youth academy system.
"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.orm import Session

from database import SessionLocal, engine
from models import Club, YouthProspect, YouthAcademyPlayer, Player
from utils.youth_academy import (
    generate_weekly_prospects,
    calculate_attribute_ranges,
    promote_academy_player,
    process_academy_week,
    assign_talent_rating,
    get_profile_picture,
    get_profile_picture_folder
)
from utils.name_generation import select_heritage_group
from utils.player_development import get_program_catalog, compile_growth_schedule, train_one_season_with_growth
from match_engine.constants import GOALKEEPER_ATTRS, OUTFIELD_ATTRS


router = APIRouter(prefix="/api/youth-academy", tags=["youth-academy"])

# ============ IN-MEMORY STORAGE (for when database is not available) ============

class InMemoryStorage:
    """In-memory storage for youth academy data when database is not available."""
    def __init__(self):
        self.prospects: Dict[str, Dict] = {}
        self.academy_players: Dict[str, Dict] = {}
        self.test_club_id: Optional[UUID] = None
        self.test_game_mode_id: Optional[UUID] = None
        self.capacity: int = 10  # Default capacity
    
    def clear(self):
        """Clear all stored data."""
        self.prospects.clear()
        self.academy_players.clear()
        self.test_club_id = None
        self.test_game_mode_id = None

# Global in-memory storage instance
_in_memory_storage = InMemoryStorage()

def get_or_create_test_club_in_memory() -> tuple:
    """Get or create test club and game mode IDs for in-memory mode."""
    if _in_memory_storage.test_club_id is None:
        _in_memory_storage.test_club_id = uuid4()
    if _in_memory_storage.test_game_mode_id is None:
        _in_memory_storage.test_game_mode_id = uuid4()
    return _in_memory_storage.test_club_id, _in_memory_storage.test_game_mode_id

# ============ IN-MEMORY STORAGE (for when database is not available) ============

class InMemoryStorage:
    """In-memory storage for youth academy data when database is not available."""
    def __init__(self):
        self.prospects: Dict[str, Dict] = {}
        self.academy_players: Dict[str, Dict] = {}
        self.test_club_id: Optional[UUID] = None
        self.test_game_mode_id: Optional[UUID] = None
        self.youth_facilities_level: int = 5  # Default for test club
    
    def clear(self):
        """Clear all stored data."""
        self.prospects.clear()
        self.academy_players.clear()
        self.test_club_id = None
        self.test_game_mode_id = None
    
    def get_capacity(self) -> int:
        """Calculate capacity based on youth facilities level."""
        return int(3 + (self.youth_facilities_level * 1.2))

# Global in-memory storage instance
_in_memory_storage = InMemoryStorage()


def get_or_create_test_club(db: Session) -> tuple:
    """Get or create test club and game mode for testing."""
    if engine is None:
        raise ValueError("Database is not configured. Please set DATABASE_URL environment variable.")
    
    from models import GameMode, Manager, League, Country, Federation
    
    # Get or create test game mode
    game_mode = db.query(GameMode).filter(GameMode.key == "classic").first()
    if not game_mode:
        game_mode = GameMode(
            key="classic",
            name="Classic",
            season_length_days=70,
            description="Test game mode",
            is_pay_to_win=False
        )
        db.add(game_mode)
        db.flush()
    
    # Get or create test manager
    test_email = "test@example.com"
    manager = db.query(Manager).filter(Manager.email == test_email).first()
    if not manager:
        manager = Manager(
            email=test_email,
            display_name="Test Manager"
        )
        db.add(manager)
        db.flush()
    
    # Get or create test league - find any existing league or create minimal one
    league = db.query(League).filter(
        League.game_mode_id == game_mode.id
    ).first()
    
    if not league:
        # Try to get a country or federation for the league
        country = db.query(Country).first()
        federation = db.query(Federation).first()
        
        # Use federation if available, otherwise country, otherwise create minimal test country
        if federation:
            league = League(
                game_mode_id=game_mode.id,
                federation_id=federation.id,
                name="Test League",
                tier=1,
                division=1,
                is_b_team_league=False,
                club_count=10,
                promote_direct=2,
                promote_playoff=0,
                relegate_direct=2,
                relegate_playoff=0
            )
        elif country:
            league = League(
                game_mode_id=game_mode.id,
                country_id=country.id,
                name="Test League",
                tier=1,
                division=1,
                is_b_team_league=False,
                club_count=10,
                promote_direct=2,
                promote_playoff=0,
                relegate_direct=2,
                relegate_playoff=0
            )
        else:
            # No country/federation exists - create minimal test federation and country
            # Check if test federation already exists (in case of previous failed attempts)
            federation = db.query(Federation).filter(Federation.key == "TEST").first()
            if not federation:
                federation = Federation(
                    key="TEST",
                    name="Test Federation"
                )
                db.add(federation)
                db.flush()
            
            # Check if test country already exists
            country = db.query(Country).filter(Country.code == "TEST").first()
            if not country:
                country = Country(
                    code="TEST",
                    name="Test Country",
                    federation_id=federation.id,
                    has_domestic_league=True,
                    ranking_points=0
                )
                db.add(country)
                db.flush()
            
            league = League(
                game_mode_id=game_mode.id,
                country_id=country.id,
                name="Test League",
                tier=1,
                division=1,
                is_b_team_league=False,
                club_count=10,
                promote_direct=2,
                promote_playoff=0,
                relegate_direct=2,
                relegate_playoff=0
            )
        
        db.add(league)
        db.flush()
    
    # Get or create test club
    club = db.query(Club).filter(
        Club.manager_id == manager.id,
        Club.game_mode_id == game_mode.id
    ).first()
    
    if not club:
        club = Club(
            manager_id=manager.id,
            game_mode_id=game_mode.id,
            league_id=league.id,
            name="Test Club",
            youth_facilities_level=5,
            training_facilities_level=5
        )
        db.add(club)
        db.flush()
    
    return club, game_mode


# ============ DEPENDENCY ============

def get_db():
    """Database session dependency."""
    if engine is None:
        # Return None to indicate in-memory mode
        yield None
        return
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============ REQUEST/RESPONSE MODELS ============

class ProspectResponse(BaseModel):
    """Response for a single prospect."""
    id: str
    name: str
    talent_rating: str
    is_goalkeeper: bool
    nationality: Optional[str]
    skin_tone: Optional[str]
    profile_pic: Optional[str]
    profile_pic_folder: Optional[str] = None  # Folder name for profile picture (e.g., "BritishIsles", "AfricaWest")
    heritage_group: Optional[str] = None  # Heritage group (e.g., "ENG_Mainstream", "ENG_WestAfrica")
    name_structure: Optional[str] = None  # Name structure (e.g., "LL", "LH", "HL", "HH")
    potential_min: int
    potential_max: int
    status: str
    week_number: int


class AcademyPlayerResponse(BaseModel):
    """Response for a single academy player."""
    id: str
    name: str
    talent_rating: str
    is_goalkeeper: bool
    nationality: Optional[str]
    skin_tone: Optional[str]
    profile_pic: Optional[str]
    profile_pic_folder: Optional[str] = None  # Folder name for profile picture
    week_joined: int
    weeks_in_academy: int
    weeks_to_promotion: int
    position: Optional[str]
    attribute_ranges: Dict[str, Dict[str, int]]
    position_traits: List[str]
    gainable_traits: List[str]
    training_program: Optional[str]
    status: str
    # Diagnostic fields (for workbench)
    actual_potential: Optional[int] = None
    birth_dev_pct: Optional[float] = None
    base_training_pct: Optional[float] = None
    growth_training_pct: Optional[float] = None
    actual_attributes: Optional[Dict[str, int]] = None


class UpdateAcademyPlayerRequest(BaseModel):
    """Request to update academy player."""
    position: Optional[str] = None
    position_traits: Optional[List[str]] = None
    gainable_traits: Optional[List[str]] = None
    training_program: Optional[str] = None


class CapacityResponse(BaseModel):
    """Response for academy capacity."""
    capacity: int
    current: int
    available: int


# ============ API ENDPOINTS ============

@router.get("/prospects", response_model=List[ProspectResponse])
@router.get("/prospects/{club_id}", response_model=List[ProspectResponse])
async def get_prospects(club_id: Optional[str] = None, db: Optional[Session] = Depends(get_db)):
    """Get available prospects for a club this week (status='available')."""
    try:
        # In-memory mode
        if db is None:
            if not club_id:
                club_uuid, _ = get_or_create_test_club_in_memory()
            else:
                try:
                    club_uuid = UUID(club_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid club_id format")
            
            # Get prospects from in-memory storage
            prospects_list = [
                p for p in _in_memory_storage.prospects.values()
                if str(p.get("club_id")) == str(club_uuid) and p.get("status") == "available"
            ]
            
            results = []
            for p in prospects_list:
                # Use stored profile_pic_folder if available, otherwise determine from heritage group
                profile_pic_folder = p.get("profile_pic_folder")
                heritage_group = None
                name_structure = None
                
                # Get heritage_group and name_structure from _player_data if available
                player_data = p.get("_player_data")
                if player_data:
                    heritage_group = player_data.get("heritage_group")
                    name_structure = player_data.get("name_structure")
                
                if not profile_pic_folder and p.get("profile_pic"):
                    if not heritage_group:
                        player_nationality = p.get("nationality", "ENG")
                        heritage_group = select_heritage_group(player_nationality)
                    profile_pic_folder = get_profile_picture_folder(heritage_group)
                
                results.append(ProspectResponse(
                    id=p["id"],
                    name=p["name"],
                    talent_rating=p["talent_rating"],
                    is_goalkeeper=p["is_goalkeeper"],
                    nationality=p.get("nationality"),
                    skin_tone=p.get("skin_tone"),
                    profile_pic=p.get("profile_pic"),
                    profile_pic_folder=profile_pic_folder,
                    heritage_group=heritage_group,
                    name_structure=name_structure,
                    potential_min=p["potential_min"],
                    potential_max=p["potential_max"],
                    status=p["status"],
                    week_number=p["week_number"]
                ))
            return results
        
        # Database mode
        if not club_id:
            try:
                club, _ = get_or_create_test_club(db)
                db.commit()
                club_uuid = club.id
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Error creating test data: {str(e)}")
        else:
            try:
                club_uuid = UUID(club_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid club_id format")
        
        club = db.query(Club).filter(Club.id == club_uuid).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        
        prospects = db.query(YouthProspect).filter(
            YouthProspect.club_id == club_uuid,
            YouthProspect.status == "available"
        ).all()
        
        results = []
        for p in prospects:
            # Determine heritage group for folder
            player_nationality = p.nationality or "ENG"
            heritage_group = select_heritage_group(player_nationality)
            profile_pic_folder = get_profile_picture_folder(heritage_group) if p.profile_pic else None
            
            # Get heritage_group and name_structure from database or determine
            heritage_group_db = heritage_group
            name_structure_db = None
            # Note: Database mode doesn't store name_structure, so we can't retrieve it
            # For new prospects, it will be set during generation
            
            results.append(ProspectResponse(
                id=str(p.id),
                name=p.name,
                talent_rating=p.talent_rating,
                is_goalkeeper=p.is_goalkeeper,
                nationality=p.nationality,
                skin_tone=p.skin_tone,
                profile_pic=p.profile_pic,
                profile_pic_folder=profile_pic_folder,
                heritage_group=heritage_group_db,
                name_structure=name_structure_db,
                potential_min=p.potential_min,
                potential_max=p.potential_max,
                status=p.status,
                week_number=p.week_number
            ))
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/prospects/{prospect_id}/promote")
async def promote_prospect(prospect_id: str, db: Optional[Session] = Depends(get_db)):
    """Promote a prospect to the youth academy."""
    try:
        import random
        
        # In-memory mode
        if db is None:
            if prospect_id not in _in_memory_storage.prospects:
                raise HTTPException(status_code=404, detail="Prospect not found")
            
            prospect = _in_memory_storage.prospects[prospect_id]
            if prospect["status"] != "available":
                raise HTTPException(status_code=400, detail=f"Prospect is not available (status: {prospect['status']})")
            
            # Check academy capacity
            club_uuid = UUID(prospect["club_id"])
            capacity = _in_memory_storage.get_capacity()
            current_count = len([
                p for p in _in_memory_storage.academy_players.values()
                if str(p.get("club_id")) == prospect["club_id"] and p.get("status") == "active"
            ])
            
            if current_count >= capacity:
                raise HTTPException(status_code=400, detail=f"Youth academy is full ({current_count}/{capacity})")
            
            # Get player data from prospect (stored during generation)
            player_data = prospect.get("_player_data")
            if not player_data:
                # Fallback: regenerate (shouldn't happen)
                from utils.player_generation import create_player_data
                player_data = create_player_data(
                    club_id=prospect["club_id"],
                    youth_facilities=_in_memory_storage.youth_facilities_level,
                    is_goalkeeper=prospect["is_goalkeeper"],
                    youth_player=False
                )
                player_data["potential"] = prospect["actual_potential"]
            
            # Create academy player in memory
            weeks_to_promotion = random.choice([4, 5])
            academy_player_id = str(uuid4())
            
            # Calculate initial ranges (week 0) - these will be asymmetric
            initial_ranges = calculate_attribute_ranges(player_data["attributes"], 0)
            
            academy_player_dict = {
                "id": academy_player_id,
                "club_id": prospect["club_id"],
                "prospect_id": prospect_id,
                "game_mode_id": prospect["game_mode_id"],
                "season_id": prospect.get("season_id"),
                "week_joined": prospect["week_number"],
                "weeks_in_academy": 0,
                "weeks_to_promotion": weeks_to_promotion,
                "name": prospect["name"],
                "is_goalkeeper": prospect["is_goalkeeper"],
                "nationality": prospect.get("nationality"),
                "skin_tone": prospect.get("skin_tone"),
                "profile_pic": prospect.get("profile_pic"),
                "talent_rating": prospect["talent_rating"],
                "actual_potential": prospect["actual_potential"],
                "actual_attributes": player_data["attributes"],
                "non_playing_attributes": player_data.get("non_playing_attributes", {}),
                "attribute_ranges": initial_ranges,
                "initial_attribute_ranges": initial_ranges,  # Store initial ranges for narrowing
                "position_traits": player_data.get("position_traits", []),
                "gainable_traits": player_data.get("gainable_traits", []),
                "position": None,
                "training_program": None,
                "status": "active",
                "birth_dev_pct": player_data.get("birth_dev_pct"),
                "base_training_pct": player_data.get("base_training_pct"),
                "growth_training_pct": player_data.get("growth_training_pct"),
                "growth_shape": player_data.get("growth_shape"),
                "growth_peak_age": player_data.get("growth_peak_age"),
                "growth_width": player_data.get("growth_width")
            }
            
            _in_memory_storage.academy_players[academy_player_id] = academy_player_dict
            
            # Update prospect status
            prospect["status"] = "promoted"
            
            return {"message": "Prospect promoted to academy", "academy_player_id": academy_player_id}
        
        # Database mode
        try:
            prospect_uuid = UUID(prospect_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid prospect_id format")
        
        prospect = db.query(YouthProspect).filter(YouthProspect.id == prospect_uuid).first()
        if not prospect:
            raise HTTPException(status_code=404, detail="Prospect not found")
        
        if prospect.status != "available":
            raise HTTPException(status_code=400, detail=f"Prospect is not available (status: {prospect.status})")
        
        # Check academy capacity
        club = db.query(Club).filter(Club.id == prospect.club_id).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        
        capacity = club.get_youth_academy_capacity()
        current_count = db.query(YouthAcademyPlayer).filter(
            YouthAcademyPlayer.club_id == prospect.club_id,
            YouthAcademyPlayer.status == "active"
        ).count()
        
        if current_count >= capacity:
            raise HTTPException(status_code=400, detail=f"Youth academy is full ({current_count}/{capacity})")
        
        # Get full player data from prospect (stored in _player_data during generation)
        from utils.player_generation import create_player_data
        
        player_data = create_player_data(
            club_id=str(prospect.club_id),
            youth_facilities=club.youth_facilities_level,
            is_goalkeeper=prospect.is_goalkeeper,
            youth_player=False
        )
        # Override potential to match prospect's actual potential
        player_data["potential"] = prospect.actual_potential
        
        # Create academy player
        weeks_to_promotion = random.choice([4, 5])
        
        # Calculate initial ranges (week 0) - these will be asymmetric
        initial_ranges = calculate_attribute_ranges(player_data["attributes"], 0)
        
        academy_player = YouthAcademyPlayer(
            club_id=prospect.club_id,
            prospect_id=prospect.id,
            game_mode_id=prospect.game_mode_id,
            season_id=prospect.season_id,
            week_joined=prospect.week_number,
            weeks_in_academy=0,
            weeks_to_promotion=weeks_to_promotion,
            name=prospect.name,
            is_goalkeeper=prospect.is_goalkeeper,
            nationality=prospect.nationality,
            skin_tone=prospect.skin_tone,
            profile_pic=prospect.profile_pic,
            talent_rating=prospect.talent_rating,
            potential=player_data["potential"],
            birth_dev_pct=player_data["birth_dev_pct"],
            base_training_pct=player_data["base_training_pct"],
            growth_training_pct=player_data["growth_training_pct"],
            growth_shape=player_data["growth_shape"],
            growth_peak_age=player_data["growth_peak_age"],
            growth_width=player_data["growth_width"],
            position=None,
            attribute_ranges=initial_ranges,
            initial_attribute_ranges=initial_ranges,  # Store initial ranges for narrowing
            position_traits=player_data["position_traits"],
            gainable_traits=player_data["gainable_traits"],
            training_program=None,
            actual_attributes=player_data["attributes"],
            non_playing_attributes=player_data["non_playing_attributes"],
            status="active"
        )
        
        db.add(academy_player)
        
        # Update prospect status
        prospect.status = "promoted"
        prospect.promoted_at = datetime.utcnow()
        
        db.commit()
        
        return {"message": "Prospect promoted to academy", "academy_player_id": str(academy_player.id)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/prospects/{prospect_id}/reject")
async def reject_prospect(prospect_id: str, db: Optional[Session] = Depends(get_db)):
    """Reject a prospect (remove from available list)."""
    try:
        # In-memory mode
        if db is None:
            if prospect_id not in _in_memory_storage.prospects:
                raise HTTPException(status_code=404, detail="Prospect not found")
            
            prospect = _in_memory_storage.prospects[prospect_id]
            if prospect["status"] != "available":
                raise HTTPException(status_code=400, detail=f"Prospect is not available (status: {prospect['status']})")
            
            prospect["status"] = "rejected"
            return {"message": "Prospect rejected"}
        
        # Database mode
        try:
            prospect_uuid = UUID(prospect_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid prospect_id format")
        
        prospect = db.query(YouthProspect).filter(YouthProspect.id == prospect_uuid).first()
        if not prospect:
            raise HTTPException(status_code=404, detail="Prospect not found")
        
        if prospect.status != "available":
            raise HTTPException(status_code=400, detail=f"Prospect is not available (status: {prospect.status})")
        
        prospect.status = "rejected"
        db.commit()
        
        return {"message": "Prospect rejected"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/prospects/reject-all")
async def reject_all_prospects(db: Optional[Session] = Depends(get_db)):
    """Reject all available prospects."""
    try:
        # In-memory mode
        if db is None:
            rejected_count = 0
            for prospect_id, prospect in _in_memory_storage.prospects.items():
                if prospect.get("status") == "available":
                    prospect["status"] = "rejected"
                    rejected_count += 1
            return {"message": "All available prospects rejected", "rejected_count": rejected_count}
        
        # Database mode
        prospects = db.query(YouthProspect).filter(YouthProspect.status == "available").all()
        rejected_count = 0
        for prospect in prospects:
            prospect.status = "rejected"
            rejected_count += 1
        db.commit()
        
        return {"message": "All available prospects rejected", "rejected_count": rejected_count}
    except Exception as e:
        if db:
            db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/players", response_model=List[AcademyPlayerResponse])
@router.get("/players/{club_id}", response_model=List[AcademyPlayerResponse])
async def get_academy_players(club_id: Optional[str] = None, db: Optional[Session] = Depends(get_db)):
    """Get all academy players for a club (status='active')."""
    try:
        # In-memory mode
        if db is None:
            if not club_id:
                club_uuid, _ = get_or_create_test_club_in_memory()
            else:
                try:
                    club_uuid = UUID(club_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid club_id format")
            
            # Get academy players from in-memory storage
            academy_players_list = [
                p for p in _in_memory_storage.academy_players.values()
                if str(p.get("club_id")) == str(club_uuid) and p.get("status") == "active"
            ]
            
            results = []
            for p in academy_players_list:
                # Determine heritage group for folder
                player_nationality = p.get("nationality", "ENG")
                heritage_group = select_heritage_group(player_nationality)
                profile_pic_folder = get_profile_picture_folder(heritage_group) if p.get("profile_pic") else None
                
                results.append(AcademyPlayerResponse(
                    id=p["id"],
                    name=p["name"],
                    talent_rating=p["talent_rating"],
                    is_goalkeeper=p["is_goalkeeper"],
                    nationality=p.get("nationality"),
                    skin_tone=p.get("skin_tone"),
                    profile_pic=p.get("profile_pic"),
                    profile_pic_folder=profile_pic_folder,
                    week_joined=p["week_joined"],
                    weeks_in_academy=p["weeks_in_academy"],
                    weeks_to_promotion=p["weeks_to_promotion"],
                    position=p.get("position"),
                    attribute_ranges=p.get("attribute_ranges", {}),
                    position_traits=p.get("position_traits", []),
                    gainable_traits=p.get("gainable_traits", []),
                    training_program=p.get("training_program"),
                    status=p["status"],
                    actual_potential=p.get("actual_potential"),
                    birth_dev_pct=p.get("birth_dev_pct"),
                    base_training_pct=p.get("base_training_pct"),
                    growth_training_pct=p.get("growth_training_pct"),
                    actual_attributes=p.get("actual_attributes")
                ))
            return results
        
        # Database mode
        if not club_id:
            club, _ = get_or_create_test_club(db)
            db.commit()
            club_uuid = club.id
        else:
            try:
                club_uuid = UUID(club_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid club_id format")
        
        club = db.query(Club).filter(Club.id == club_uuid).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        
        academy_players = db.query(YouthAcademyPlayer).filter(
            YouthAcademyPlayer.club_id == club_uuid,
            YouthAcademyPlayer.status == "active"
        ).all()
        
        results = []
        for p in academy_players:
            # Determine heritage group for folder
            player_nationality = p.nationality or "ENG"
            heritage_group = select_heritage_group(player_nationality)
            profile_pic_folder = get_profile_picture_folder(heritage_group) if p.profile_pic else None
            
            results.append(AcademyPlayerResponse(
                id=str(p.id),
                name=p.name,
                talent_rating=p.talent_rating,
                is_goalkeeper=p.is_goalkeeper,
                nationality=p.nationality,
                skin_tone=p.skin_tone,
                profile_pic=p.profile_pic,
                profile_pic_folder=profile_pic_folder,
                week_joined=p.week_joined,
                weeks_in_academy=p.weeks_in_academy,
                weeks_to_promotion=p.weeks_to_promotion,
                position=p.position,
                attribute_ranges=p.attribute_ranges or {},
                position_traits=p.position_traits or [],
                gainable_traits=p.gainable_traits or [],
                training_program=p.training_program,
                status=p.status,
                actual_potential=p.potential,
                birth_dev_pct=p.birth_dev_pct,
                base_training_pct=p.base_training_pct,
                growth_training_pct=p.growth_training_pct,
                actual_attributes=p.actual_attributes
            ))
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.patch("/players/{academy_player_id}")
async def update_academy_player(
    academy_player_id: str,
    request: UpdateAcademyPlayerRequest,
    db: Session = Depends(get_db)
):
    """Update academy player (position, traits, training program)."""
    try:
        player_uuid = UUID(academy_player_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid academy_player_id format")
    
    academy_player = db.query(YouthAcademyPlayer).filter(
        YouthAcademyPlayer.id == player_uuid
    ).first()
    
    if not academy_player:
        raise HTTPException(status_code=404, detail="Academy player not found")
    
    if academy_player.status != "active":
        raise HTTPException(status_code=400, detail=f"Academy player is not active (status: {academy_player.status})")
    
    # Update fields if provided
    if request.position is not None:
        academy_player.position = request.position
    
    if request.position_traits is not None:
        academy_player.position_traits = request.position_traits
    
    if request.gainable_traits is not None:
        academy_player.gainable_traits = request.gainable_traits
    
    if request.training_program is not None:
        # Validate training program
        program_catalog = get_program_catalog(academy_player.is_goalkeeper)
        if request.training_program not in program_catalog:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid training program: {request.training_program}. Available: {list(program_catalog.keys())}"
            )
        academy_player.training_program = request.training_program
    
    db.commit()
    
    return {"message": "Academy player updated"}


@router.post("/players/{academy_player_id}/release")
async def release_academy_player(academy_player_id: str, db: Session = Depends(get_db)):
    """Release an academy player."""
    try:
        player_uuid = UUID(academy_player_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid academy_player_id format")
    
    academy_player = db.query(YouthAcademyPlayer).filter(
        YouthAcademyPlayer.id == player_uuid
    ).first()
    
    if not academy_player:
        raise HTTPException(status_code=404, detail="Academy player not found")
    
    if academy_player.status != "active":
        raise HTTPException(status_code=400, detail=f"Academy player is not active (status: {academy_player.status})")
    
    academy_player.status = "released"
    db.commit()
    
    return {"message": "Academy player released"}


@router.post("/players/{academy_player_id}/promote")
async def promote_academy_player_endpoint(academy_player_id: str, db: Session = Depends(get_db)):
    """Promote an academy player to the main team (early promotion)."""
    try:
        player_uuid = UUID(academy_player_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid academy_player_id format")
    
    academy_player = db.query(YouthAcademyPlayer).filter(
        YouthAcademyPlayer.id == player_uuid
    ).first()
    
    if not academy_player:
        raise HTTPException(status_code=404, detail="Academy player not found")
    
    if academy_player.status != "active":
        raise HTTPException(status_code=400, detail=f"Academy player is not active (status: {academy_player.status})")
    
    # Promote to main team
    player = promote_academy_player(academy_player, db)
    db.commit()
    
    return {"message": "Academy player promoted to main team", "player_id": str(player.id)}


@router.get("/capacity", response_model=CapacityResponse)
@router.get("/capacity/{club_id}", response_model=CapacityResponse)
async def get_academy_capacity(club_id: Optional[str] = None, db: Optional[Session] = Depends(get_db)):
    """Get youth academy capacity for a club."""
    try:
        # In-memory mode
        if db is None:
            if not club_id:
                club_uuid, _ = get_or_create_test_club_in_memory()
            else:
                try:
                    club_uuid = UUID(club_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid club_id format")
            
            capacity = _in_memory_storage.get_capacity()
            current = len([
                p for p in _in_memory_storage.academy_players.values()
                if str(p.get("club_id")) == str(club_uuid) and p.get("status") == "active"
            ])
            
            return CapacityResponse(
                capacity=capacity,
                current=current,
                available=max(0, capacity - current)
            )
        
        # Database mode
        if not club_id:
            try:
                club, _ = get_or_create_test_club(db)
                db.commit()
                club_uuid = club.id
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Error creating test data: {str(e)}")
        else:
            try:
                club_uuid = UUID(club_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid club_id format")
        
        club = db.query(Club).filter(Club.id == club_uuid).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        
        capacity = club.get_youth_academy_capacity()
        current = db.query(YouthAcademyPlayer).filter(
            YouthAcademyPlayer.club_id == club_uuid,
            YouthAcademyPlayer.status == "active"
        ).count()
        
        return CapacityResponse(
            capacity=capacity,
            current=current,
            available=max(0, capacity - current)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


class GenerateProspectsRequest(BaseModel):
    """Request to generate weekly prospects."""
    club_id: Optional[str] = None
    game_mode_id: Optional[str] = None
    season_id: Optional[str] = None
    week_number: int = Field(default=1, ge=1)
    youth_facilities_level: int = Field(default=5, ge=0, le=10)
    is_goalkeeper: bool = False
    num_prospects: int = Field(default=8, ge=1, le=20)
    min_potential: Optional[int] = Field(default=None, ge=200, le=3000, description="Minimum potential for prospect generation")
    max_potential: Optional[int] = Field(default=None, ge=200, le=3000, description="Maximum potential for prospect generation")
    use_potential_range: bool = Field(default=False, description="If True, generate potential uniformly within range instead of using youth facilities distribution")
    nationality: Optional[str] = Field(default=None, description="Nationality code for all prospects (e.g., 'ENG', 'NGA')")
    heritage_options: Optional[List[str]] = Field(default=None, description="List of heritage country codes to choose from (e.g., ['ENG', 'NGA'])")


@router.post("/generate-prospects")
async def generate_prospects_endpoint(request: GenerateProspectsRequest, db: Optional[Session] = Depends(get_db)):
    """Generate weekly prospects for testing (workbench endpoint)."""
    try:
        # In-memory mode
        if db is None:
            if not request.club_id or not request.game_mode_id:
                club_uuid, game_mode_uuid = get_or_create_test_club_in_memory()
                _in_memory_storage.youth_facilities_level = request.youth_facilities_level
            else:
                try:
                    club_uuid = UUID(request.club_id)
                    game_mode_uuid = UUID(request.game_mode_id)
                except ValueError as e:
                    raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")
            
            season_uuid = UUID(request.season_id) if request.season_id else None
            
            # Generate prospects with potential filtering if specified
            prospect_data_list = []
            
            if request.use_potential_range and request.min_potential is not None and request.max_potential is not None:
                # Generate potential uniformly within range
                import random as rnd
                for _ in range(request.num_prospects):
                    # Generate a prospect normally, then override potential
                    temp_prospects = generate_weekly_prospects(
                        club_id=club_uuid,
                        game_mode_id=game_mode_uuid,
                        season_id=season_uuid,
                        week_number=request.week_number,
                        youth_facilities_level=request.youth_facilities_level,
                        is_goalkeeper=request.is_goalkeeper,
                        nationality=request.nationality,
                        heritage_options=request.heritage_options
                    )
                    if temp_prospects:
                        prospect = temp_prospects[0]
                        # Override potential with uniformly distributed value
                        new_potential = rnd.randint(request.min_potential, request.max_potential)
                        prospect["actual_potential"] = new_potential
                        # Re-assign talent rating based on new potential
                        talent_rating, potential_min, potential_max = assign_talent_rating(
                            new_potential, request.is_goalkeeper
                        )
                        prospect["talent_rating"] = talent_rating
                        prospect["potential_min"] = potential_min
                        prospect["potential_max"] = potential_max
                        # Update player data potential and regenerate attributes
                        if "_player_data" in prospect:
                            from utils.player_generation import apply_birth_development
                            prospect["_player_data"]["potential"] = new_potential
                            # Regenerate attributes with new potential but keep existing birth_dev_pct
                            birth_dev_pct = prospect["_player_data"].get("birth_dev_pct", 0.25)
                            attrs, nom, asg = apply_birth_development(
                                is_gk=request.is_goalkeeper,
                                potential=new_potential,
                                birth_dev_pct=birth_dev_pct
                            )
                            prospect["_player_data"]["attributes"] = attrs
                        prospect_data_list.append(prospect)
            else:
                # Filter by potential range if specified
                max_attempts = request.num_prospects * 50
                attempts = 0
                
                while len(prospect_data_list) < request.num_prospects and attempts < max_attempts:
                    attempts += 1
                    temp_prospects = generate_weekly_prospects(
                        club_id=club_uuid,
                        game_mode_id=game_mode_uuid,
                        season_id=season_uuid,
                        week_number=request.week_number,
                        youth_facilities_level=request.youth_facilities_level,
                        is_goalkeeper=request.is_goalkeeper,
                        nationality=request.nationality,
                        heritage_options=request.heritage_options
                    )
                    
                    for prospect in temp_prospects:
                        if len(prospect_data_list) >= request.num_prospects:
                            break
                        # Filter by potential if range specified
                        if request.min_potential is not None and request.max_potential is not None:
                            if request.min_potential <= prospect["actual_potential"] <= request.max_potential:
                                prospect_data_list.append(prospect)
                        else:
                            # No filter, accept all
                            prospect_data_list.append(prospect)
                
                # If we have fewer than requested, log a warning but continue
                if len(prospect_data_list) < request.num_prospects:
                    import logging
                    logging.warning(
                        f"Only generated {len(prospect_data_list)} out of {request.num_prospects} requested prospects "
                        f"within potential range {request.min_potential}-{request.max_potential} after {attempts} attempts. "
                        f"Consider enabling 'Use Potential Range Directly' for guaranteed results."
                    )
            
            prospect_data_list = prospect_data_list[:request.num_prospects]
            
            # Store in memory
            created_prospects = []
            for prospect_data in prospect_data_list:
                player_data = prospect_data.pop("_player_data", None)
                prospect_id = str(uuid4())
                
                # Use heritage_group from player_data if available (set during name generation)
                # Otherwise determine it from nationality
                heritage_group = None
                if player_data and player_data.get("heritage_group"):
                    heritage_group = player_data.get("heritage_group")
                else:
                    player_nationality = prospect_data.get("nationality", "ENG")
                    heritage_group = select_heritage_group(player_nationality)
                
                profile_pic_folder = get_profile_picture_folder(heritage_group) if prospect_data.get("profile_pic") else None
                
                prospect_dict = {
                    "id": prospect_id,
                    "club_id": str(club_uuid),
                    "game_mode_id": str(game_mode_uuid),
                    "season_id": str(season_uuid) if season_uuid else None,
                    "week_number": prospect_data["week_number"],
                    "name": prospect_data["name"],
                    "talent_rating": prospect_data["talent_rating"],
                    "is_goalkeeper": prospect_data["is_goalkeeper"],
                    "nationality": prospect_data.get("nationality"),
                    "skin_tone": prospect_data.get("skin_tone"),
                    "profile_pic": prospect_data.get("profile_pic"),
                    "profile_pic_folder": profile_pic_folder,
                    "potential_min": prospect_data["potential_min"],
                    "potential_max": prospect_data["potential_max"],
                    "actual_potential": prospect_data["actual_potential"],
                    "status": "available",
                    "_player_data": player_data
                }
                _in_memory_storage.prospects[prospect_id] = prospect_dict
                
                # Get name_structure from player_data if available
                name_structure = None
                if player_data:
                    name_structure = player_data.get("name_structure")
                
                created_prospects.append(ProspectResponse(
                    id=prospect_id,
                    name=prospect_dict["name"],
                    talent_rating=prospect_dict["talent_rating"],
                    is_goalkeeper=prospect_dict["is_goalkeeper"],
                    nationality=prospect_dict["nationality"],
                    skin_tone=prospect_dict["skin_tone"],
                    profile_pic=prospect_dict["profile_pic"],
                    profile_pic_folder=profile_pic_folder,
                    heritage_group=heritage_group,
                    name_structure=name_structure,
                    potential_min=prospect_dict["potential_min"],
                    potential_max=prospect_dict["potential_max"],
                    status=prospect_dict["status"],
                    week_number=prospect_dict["week_number"]
                ))
            
            return {
                "prospects": created_prospects,
                "count": len(created_prospects),
                "club_id": str(club_uuid),
                "game_mode_id": str(game_mode_uuid)
            }
        
        # Database mode
        if not request.club_id or not request.game_mode_id:
            try:
                club, game_mode = get_or_create_test_club(db)
                club_uuid = club.id
                game_mode_uuid = game_mode.id
                db.commit()
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail=f"Error creating test data: {str(e)}")
        else:
            try:
                club_uuid = UUID(request.club_id)
                game_mode_uuid = UUID(request.game_mode_id)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")
            club = db.query(Club).filter(Club.id == club_uuid).first()
            if not club:
                raise HTTPException(status_code=404, detail="Club not found")
        
        season_uuid = UUID(request.season_id) if request.season_id else None
        
        # Generate prospects with potential filtering if specified
        prospect_data_list = []
        
        if request.use_potential_range and request.min_potential is not None and request.max_potential is not None:
            # Generate potential uniformly within range
            import random as rnd
            for _ in range(request.num_prospects):
                # Generate a prospect normally, then override potential
                temp_prospects = generate_weekly_prospects(
                    club_id=club_uuid,
                    game_mode_id=game_mode_uuid,
                    season_id=season_uuid,
                    week_number=request.week_number,
                    youth_facilities_level=request.youth_facilities_level,
                    is_goalkeeper=request.is_goalkeeper,
                    nationality=request.nationality,
                    heritage_options=request.heritage_options
                )
                if temp_prospects:
                    prospect = temp_prospects[0]
                    # Override potential with uniformly distributed value
                    new_potential = rnd.randint(request.min_potential, request.max_potential)
                    prospect["actual_potential"] = new_potential
                    # Re-assign talent rating based on new potential
                    talent_rating, potential_min, potential_max = assign_talent_rating(
                        new_potential, request.is_goalkeeper
                    )
                    prospect["talent_rating"] = talent_rating
                    prospect["potential_min"] = potential_min
                    prospect["potential_max"] = potential_max
                    # Update player data potential and regenerate attributes
                    if "_player_data" in prospect:
                        from utils.player_generation import apply_birth_development
                        prospect["_player_data"]["potential"] = new_potential
                        # Regenerate attributes with new potential but keep existing birth_dev_pct
                        birth_dev_pct = prospect["_player_data"].get("birth_dev_pct", 0.25)
                        attrs, nom, asg = apply_birth_development(
                            is_gk=request.is_goalkeeper,
                            potential=new_potential,
                            birth_dev_pct=birth_dev_pct
                        )
                        prospect["_player_data"]["attributes"] = attrs
                    prospect_data_list.append(prospect)
        else:
            # Filter by potential range if specified
            max_attempts = request.num_prospects * 50
            attempts = 0
            
            while len(prospect_data_list) < request.num_prospects and attempts < max_attempts:
                attempts += 1
                temp_prospects = generate_weekly_prospects(
                    club_id=club_uuid,
                    game_mode_id=game_mode_uuid,
                    season_id=season_uuid,
                    week_number=request.week_number,
                    youth_facilities_level=request.youth_facilities_level,
                    is_goalkeeper=request.is_goalkeeper,
                    nationality=request.nationality,
                    heritage_options=request.heritage_options
                )
                
                for prospect in temp_prospects:
                    if len(prospect_data_list) >= request.num_prospects:
                        break
                    # Filter by potential if range specified
                    if request.min_potential is not None and request.max_potential is not None:
                        if request.min_potential <= prospect["actual_potential"] <= request.max_potential:
                            prospect_data_list.append(prospect)
                    else:
                        # No filter, accept all
                        prospect_data_list.append(prospect)
            
            # If we have fewer than requested, log a warning but continue
            if len(prospect_data_list) < request.num_prospects:
                import logging
                logging.warning(
                    f"Only generated {len(prospect_data_list)} out of {request.num_prospects} requested prospects "
                    f"within potential range {request.min_potential}-{request.max_potential} after {attempts} attempts. "
                    f"Consider enabling 'Use Potential Range Directly' for guaranteed results."
                )
        
        prospect_data_list = prospect_data_list[:request.num_prospects]
        
        created_prospects = []
        for prospect_data in prospect_data_list:
            player_data = prospect_data.pop("_player_data", None)
            prospect = YouthProspect(**prospect_data)
            db.add(prospect)
            db.flush()
            # Determine heritage group for folder
            player_nationality = prospect.nationality or "ENG"
            heritage_group = select_heritage_group(player_nationality)
            profile_pic_folder = get_profile_picture_folder(heritage_group) if prospect.profile_pic else None
            
            # Get name_structure from player_data if available (for database mode, this may not be stored)
            name_structure_db = None
            # Note: For database mode, name_structure is not stored, so it will be None for existing prospects
            
            created_prospects.append(ProspectResponse(
                id=str(prospect.id),
                name=prospect.name,
                talent_rating=prospect.talent_rating,
                is_goalkeeper=prospect.is_goalkeeper,
                nationality=prospect.nationality,
                skin_tone=prospect.skin_tone,
                profile_pic=prospect.profile_pic,
                profile_pic_folder=profile_pic_folder,
                heritage_group=heritage_group,
                name_structure=name_structure_db,
                potential_min=prospect.potential_min,
                potential_max=prospect.potential_max,
                status=prospect.status,
                week_number=prospect.week_number
            ))
        
        db.commit()
        
        return {
            "prospects": created_prospects,
            "count": len(created_prospects),
            "club_id": str(club_uuid),
            "game_mode_id": str(game_mode_uuid)
        }
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid UUID format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/progress-week", response_model=dict)
@router.post("/progress-week/{club_id}", response_model=dict)
async def progress_week(club_id: Optional[str] = None, db: Optional[Session] = Depends(get_db)):
    """Progress all academy players by one week (for testing)."""
    try:
        # In-memory mode
        if db is None:
            if not club_id:
                club_uuid, _ = get_or_create_test_club_in_memory()
            else:
                try:
                    club_uuid = UUID(club_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid club_id format")
            
            # Get academy players from in-memory storage
            academy_players_list = [
                p for p in _in_memory_storage.academy_players.values()
                if str(p.get("club_id")) == str(club_uuid) and p.get("status") == "active"
            ]
            
            if not academy_players_list:
                return {"message": "No active academy players to progress", "progressed": 0}
            
            # Process one week for all players
            for player in academy_players_list:
                player["weeks_in_academy"] += 1
                # Recalculate attribute ranges (narrowing from initial ranges)
                if player.get("actual_attributes"):
                    initial_ranges = player.get("initial_attribute_ranges")
                    player["attribute_ranges"] = calculate_attribute_ranges(
                        player["actual_attributes"],
                        player["weeks_in_academy"],
                        initial_ranges=initial_ranges
                    )
                
                # Auto-promote if weeks >= weeks_to_promotion
                if player["weeks_in_academy"] >= player["weeks_to_promotion"]:
                    player["status"] = "promoted"  # Mark as promoted (in real system would create Player)
            
            return {
                "message": f"Progressed {len(academy_players_list)} academy player(s) by one week",
                "progressed": len(academy_players_list)
            }
        
        # Database mode
        if not club_id:
            club, _ = get_or_create_test_club(db)
            db.commit()
            club_uuid = club.id
        else:
            try:
                club_uuid = UUID(club_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid club_id format")
        
        club = db.query(Club).filter(Club.id == club_uuid).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        
        academy_players = db.query(YouthAcademyPlayer).filter(
            YouthAcademyPlayer.club_id == club_uuid,
            YouthAcademyPlayer.status == "active"
        ).all()
        
        if not academy_players:
            return {"message": "No active academy players to progress", "progressed": 0}
        
        # Process one week for all players
        for player in academy_players:
            player.weeks_in_academy += 1
            # Recalculate attribute ranges (narrowing from initial ranges)
            if player.actual_attributes:
                initial_ranges = player.initial_attribute_ranges
                player.attribute_ranges = calculate_attribute_ranges(
                    player.actual_attributes,
                    player.weeks_in_academy,
                    initial_ranges=initial_ranges
                )
            
            # Auto-promote if weeks >= weeks_to_promotion
            if player.weeks_in_academy >= player.weeks_to_promotion:
                promote_academy_player(player, db)
        
        db.commit()
        
        return {
            "message": f"Progressed {len(academy_players)} academy player(s) by one week",
            "progressed": len(academy_players)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


class PromotedPlayerResponse(BaseModel):
    """Response for a promoted player (from academy to main team)."""
    id: str
    name: str
    is_goalkeeper: bool
    nationality: Optional[str]
    skin_tone: Optional[str]
    profile_pic: Optional[str]
    profile_pic_folder: Optional[str] = None  # Folder name for profile picture
    position: Optional[str]
    actual_attributes: Dict[str, int]
    non_playing_attributes: Optional[Dict[str, Any]]
    position_traits: List[str]
    gainable_traits: List[str]
    potential: int
    birth_dev_pct: Optional[float]
    base_training_pct: Optional[float]
    growth_training_pct: Optional[float]
    promoted_at: Optional[str]


@router.get("/promoted-players", response_model=List[PromotedPlayerResponse])
@router.get("/promoted-players/{club_id}", response_model=List[PromotedPlayerResponse])
async def get_promoted_players(club_id: Optional[str] = None, db: Optional[Session] = Depends(get_db)):
    """Get all promoted players (from academy to main team)."""
    try:
        # In-memory mode
        if db is None:
            if not club_id:
                club_uuid, _ = get_or_create_test_club_in_memory()
            else:
                try:
                    club_uuid = UUID(club_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid club_id format")
            
            # Get promoted academy players from in-memory storage
            promoted_players_list = [
                p for p in _in_memory_storage.academy_players.values()
                if str(p.get("club_id")) == str(club_uuid) and p.get("status") == "promoted"
            ]
            
            results = []
            for p in promoted_players_list:
                # Determine heritage group for folder
                player_nationality = p.get("nationality", "ENG")
                heritage_group = select_heritage_group(player_nationality)
                profile_pic_folder = get_profile_picture_folder(heritage_group) if p.get("profile_pic") else None
                
                results.append(PromotedPlayerResponse(
                    id=p["id"],
                    name=p["name"],
                    is_goalkeeper=p["is_goalkeeper"],
                    nationality=p.get("nationality"),
                    skin_tone=p.get("skin_tone"),
                    profile_pic=p.get("profile_pic"),
                    profile_pic_folder=profile_pic_folder,
                    position=p.get("position"),
                    actual_attributes=p.get("actual_attributes", {}),
                    non_playing_attributes=p.get("non_playing_attributes", {}),
                    position_traits=p.get("position_traits", []),
                    gainable_traits=p.get("gainable_traits", []),
                    potential=p.get("actual_potential", 0),
                    birth_dev_pct=p.get("birth_dev_pct"),
                    base_training_pct=p.get("base_training_pct"),
                    growth_training_pct=p.get("growth_training_pct"),
                    promoted_at=None
                ))
            return results
        
        # Database mode
        if not club_id:
            club, _ = get_or_create_test_club(db)
            db.commit()
            club_uuid = club.id
        else:
            try:
                club_uuid = UUID(club_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid club_id format")
        
        club = db.query(Club).filter(Club.id == club_uuid).first()
        if not club:
            raise HTTPException(status_code=404, detail="Club not found")
        
        # Get promoted academy players
        promoted_academy_players = db.query(YouthAcademyPlayer).filter(
            YouthAcademyPlayer.club_id == club_uuid,
            YouthAcademyPlayer.status == "promoted"
        ).all()
        
        # Get corresponding Player records
        promoted_players = []
        for academy_player in promoted_academy_players:
            if academy_player.promoted_to_player_id:
                player = db.query(Player).filter(Player.id == academy_player.promoted_to_player_id).first()
                if player:
                    # Determine heritage group for folder
                    player_nationality = player.nationality or "ENG"
                    heritage_group = select_heritage_group(player_nationality)
                    profile_pic_folder = get_profile_picture_folder(heritage_group) if academy_player.profile_pic else None
                    
                    promoted_players.append(PromotedPlayerResponse(
                        id=str(player.id),
                        name=player.name,
                        is_goalkeeper=player.is_goalkeeper,
                        nationality=player.nationality,
                        skin_tone=player.skin_tone,
                        profile_pic=academy_player.profile_pic,  # Use academy pic
                        profile_pic_folder=profile_pic_folder,
                        position=player.position,
                        actual_attributes=player.attributes or {},
                        non_playing_attributes=player.non_playing_attributes or {},
                        position_traits=player.position_traits or [],
                        gainable_traits=player.gainable_traits or [],
                        potential=player.potential,
                        birth_dev_pct=player.birth_dev_pct,
                        base_training_pct=player.base_training_pct,
                        growth_training_pct=player.growth_training_pct,
                        promoted_at=academy_player.promoted_at.isoformat() if academy_player.promoted_at else None
                    ))
        
        return promoted_players
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


class TrainPromotedPlayersRequest(BaseModel):
    """Request to train promoted players for development."""
    club_id: Optional[str] = None
    training_facilities: int = Field(default=10, ge=0, le=10)
    primary_program: Optional[str] = "Balanced"
    primary_share: float = Field(default=0.4, ge=0, le=1)
    secondary_program: Optional[str] = "Balanced"
    secondary_share: float = Field(default=0.2, ge=0, le=1)
    general_share: float = Field(default=0.4, ge=0, le=1)
    years_to_simulate: int = Field(default=1, ge=1, le=20, description="Number of years to train (from 16y1)")


class TrainPromotedPlayersResponse(BaseModel):
    """Response from training promoted players."""
    players: List[Dict]  # List of player snapshots per year
    development_points: List[Dict]  # DP breakdown per year


@router.post("/train-promoted-players", response_model=TrainPromotedPlayersResponse)
async def train_promoted_players(request: TrainPromotedPlayersRequest, db: Optional[Session] = Depends(get_db)):
    """
    Train promoted players from 16y1 for specified number of years.
    Returns yearly snapshots of player attributes and development points.
    """
    try:
        # Get promoted players
        if db is None:
            # In-memory mode
            if not request.club_id:
                club_uuid, _ = get_or_create_test_club_in_memory()
            else:
                try:
                    club_uuid = UUID(request.club_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid club_id format")
            
            promoted_players_list = [
                p for p in _in_memory_storage.academy_players.values()
                if str(p.get("club_id")) == str(club_uuid) and p.get("status") == "promoted"
            ]
            
            if not promoted_players_list:
                raise HTTPException(status_code=404, detail="No promoted players found")
            
            # Convert to SimplePlayer format
            class SimplePlayer:
                def __init__(self, data):
                    self.id = uuid4()
                    self.potential = data.get("actual_potential", 2000)
                    self.birth_dev_pct = data.get("birth_dev_pct", 0.15)
                    self.base_training_pct = data.get("base_training_pct", 0.40)
                    self.growth_training_pct = data.get("growth_training_pct", 0.45)
                    self.growth_shape = data.get("growth_shape", 2.0)
                    self.growth_peak_age = data.get("growth_peak_age", 22.0)
                    self.growth_width = data.get("growth_width", 4.0)
                    self.attributes = data.get("actual_attributes", {}).copy()
                    # Ensure they start at 16y1 (193 months, 1 training week)
                    self.actual_age_months = 16 * 12 + 1
                    self.training_age_weeks = 1
                    self.is_goalkeeper = data.get("is_goalkeeper", False)
                    self.name = data.get("name", "Player")
                    self.nationality = data.get("nationality", "ENG")
                    self.profile_pic = data.get("profile_pic")
            
            players = [SimplePlayer(p) for p in promoted_players_list]
        else:
            # Database mode
            if not request.club_id:
                club, _ = get_or_create_test_club(db)
                db.commit()
                club_uuid = club.id
            else:
                try:
                    club_uuid = UUID(request.club_id)
                except ValueError:
                    raise HTTPException(status_code=400, detail="Invalid club_id format")
            
            club = db.query(Club).filter(Club.id == club_uuid).first()
            if not club:
                raise HTTPException(status_code=404, detail="Club not found")
            
            # Get promoted academy players
            promoted_academy_players = db.query(YouthAcademyPlayer).filter(
                YouthAcademyPlayer.club_id == club_uuid,
                YouthAcademyPlayer.status == "promoted"
            ).all()
            
            if not promoted_academy_players:
                raise HTTPException(status_code=404, detail="No promoted players found")
            
            # Get corresponding Player records
            class SimplePlayer:
                def __init__(self, academy_player, player):
                    self.id = player.id
                    self.potential = player.potential
                    self.birth_dev_pct = player.birth_dev_pct
                    self.base_training_pct = player.base_training_pct
                    self.growth_training_pct = player.growth_training_pct
                    self.growth_shape = player.growth_shape
                    self.growth_peak_age = player.growth_peak_age
                    self.growth_width = player.growth_width
                    self.attributes = (player.attributes or {}).copy()
                    # Ensure they start at 16y1 (193 months, 1 training week)
                    self.actual_age_months = 16 * 12 + 1
                    self.training_age_weeks = 1
                    self.is_goalkeeper = player.is_goalkeeper
                    self.name = player.name
                    self.nationality = player.nationality
                    self.profile_pic = academy_player.profile_pic
            
            players = []
            for academy_player in promoted_academy_players:
                if academy_player.promoted_to_player_id:
                    player = db.query(Player).filter(Player.id == academy_player.promoted_to_player_id).first()
                    if player:
                        players.append(SimplePlayer(academy_player, player))
            
            if not players:
                raise HTTPException(status_code=404, detail="No promoted player records found")
        
        # Pre-compute growth schedules
        growth_caches = {}
        train_carries = {}
        for player in players:
            player_id = str(player.id)
            growth_caches[player_id] = compile_growth_schedule(
                player.growth_shape,
                player.growth_peak_age,
                total_weeks=160
            )
            attrs_list = GOALKEEPER_ATTRS if player.is_goalkeeper else OUTFIELD_ATTRS
            train_carries[player_id] = {a: 0.0 for a in attrs_list}
        
        # Track yearly snapshots
        yearly_snapshots = []
        yearly_dp_breakdown = []
        
        # Initial snapshot (16y1)
        year = 16
        month = 1
        snapshot = {
            "year": year,
            "month": month,
            "players": []
        }
        dp_breakdown = {
            "year": year,
            "month": month,
            "players": []
        }
        
        for player in players:
            # Determine heritage group for folder
            player_nationality = getattr(player, 'nationality', None) or "ENG"
            heritage_group = select_heritage_group(player_nationality)
            profile_pic = getattr(player, 'profile_pic', None)
            profile_pic_folder = get_profile_picture_folder(heritage_group) if profile_pic else None
            
            snapshot["players"].append({
                "name": player.name,
                "age_months": player.actual_age_months,
                "training_weeks": player.training_age_weeks,
                "attributes": player.attributes.copy(),
                "potential": player.potential,
                "profile_pic": profile_pic,
                "profile_pic_folder": profile_pic_folder
            })
            # Calculate DP pools at this age
            total_base = player.potential * player.base_training_pct
            total_growth = player.potential * player.growth_training_pct
            dp_breakdown["players"].append({
                "name": player.name,
                "birth_dp": player.potential * player.birth_dev_pct,
                "base_training_total": total_base,
                "growth_training_total": total_growth,
                "base_training_this_year": 0.0,
                "growth_training_this_year": 0.0,
                "nominal_used_this_year": 0.0,
                "assigned_dp_this_year": 0.0
            })
        
        yearly_snapshots.append(snapshot)
        yearly_dp_breakdown.append(dp_breakdown)
        
        # Simulate years (each year = 10 training weeks + offseason)
        for year_num in range(1, request.years_to_simulate + 1):
            # Capture training weeks before training for each player
            player_training_weeks_before = {}
            for player in players:
                player_id = str(player.id)
                player_training_weeks_before[player_id] = player.training_age_weeks
            
            # Train for 10 weeks (1 season)
            season_totals = train_one_season_with_growth(
                players,
                growth_caches,
                train_carries,
                training_facilities_level=request.training_facilities,
                primary_program=request.primary_program,
                primary_share=request.primary_share,
                secondary_program=request.secondary_program,
                secondary_share=request.secondary_share,
                general_share=request.general_share,
                season_weeks=10,
                total_weeks=160,
                DP_PER_ATTR_POINT=10.0
            )
            
            # Calculate current year
            current_year = 16 + year_num
            current_month = 1
            
            snapshot = {
                "year": current_year,
                "month": current_month,
                "players": []
            }
            dp_breakdown = {
                "year": current_year,
                "month": current_month,
                "players": []
            }
            
            for player in players:
                player_id = str(player.id)
                nom_total, asg_total = season_totals.get(player_id, (0.0, 0.0))
                
                # Determine heritage group for folder
                player_nationality = getattr(player, 'nationality', None) or "ENG"
                heritage_group = select_heritage_group(player_nationality)
                profile_pic = getattr(player, 'profile_pic', None)
                profile_pic_folder = get_profile_picture_folder(heritage_group) if profile_pic else None
                
                snapshot["players"].append({
                    "name": player.name,
                    "age_months": player.actual_age_months,
                    "training_weeks": player.training_age_weeks,
                    "attributes": player.attributes.copy(),
                    "potential": player.potential,
                    "profile_pic": profile_pic,
                    "profile_pic_folder": profile_pic_folder
                })
                
                # Calculate DP breakdown for this year
                total_base = player.potential * player.base_training_pct
                total_growth = player.potential * player.growth_training_pct
                base_per_week = total_base / 160 if player.training_age_weeks <= 160 else 0.0
                
                # Growth DP this year (sum of the 10 weeks we just trained)
                # Note: train_player_week uses training_age_weeks directly as index (not training_age_weeks - 1)
                # So if training_age_weeks = 1, it uses cache[1] (week 2), then increments to 2
                # If we started at training_week_before = 1 and trained 10 weeks:
                # - Used cache indices: [1, 2, 3, ..., 10] (which are weeks 2-11 in the cache)
                growth_this_year = 0.0
                training_week_before = player_training_weeks_before[player_id]
                if player.training_age_weeks <= 160:
                    # train_player_week uses the current training_age_weeks as the index before incrementing
                    # So we use indices training_week_before to (training_week_before + 9) inclusive
                    start_idx = training_week_before
                    end_idx = min(training_week_before + 10, len(growth_caches[player_id]))
                    for idx in range(start_idx, end_idx):
                        if 0 <= idx < len(growth_caches[player_id]):
                            growth_this_year += total_growth * growth_caches[player_id][idx]
                
                base_this_year = base_per_week * 10 if player.training_age_weeks <= 160 else 0.0
                
                dp_breakdown["players"].append({
                    "name": player.name,
                    "birth_dp": player.potential * player.birth_dev_pct,
                    "base_training_total": total_base,
                    "growth_training_total": total_growth,
                    "base_training_this_year": base_this_year,
                    "growth_training_this_year": growth_this_year,
                    "nominal_used_this_year": nom_total,
                    "assigned_dp_this_year": asg_total
                })
            
            yearly_snapshots.append(snapshot)
            yearly_dp_breakdown.append(dp_breakdown)
        
        return TrainPromotedPlayersResponse(
            players=yearly_snapshots,
            development_points=yearly_dp_breakdown
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/random-profile-picture")
async def get_random_profile_picture():
    """Get a random profile picture filename from the profile pictures folder."""
    profile_pic, profile_pic_folder = get_profile_picture()
    if profile_pic is None:
        raise HTTPException(status_code=404, detail="No profile pictures found")
    folder = profile_pic_folder or "Anglosphere"
    return {"filename": profile_pic, "folder": folder, "path": f"/gfx/{folder}/{profile_pic}"}


@router.get("/", response_class=HTMLResponse)
async def youth_academy_ui():
    """Serve the youth academy workbench UI."""
    try:
        with open("templates/youth_academy_workbench.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Youth Academy Workbench UI not found</h1><p>Please create templates/youth_academy_workbench.html</p>",
            status_code=404
        )
