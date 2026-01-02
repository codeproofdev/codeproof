"""
Setup routes
Handles initial application setup (first admin creation)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import User, UserRole, Category, Subcategory
from app.schemas import SetupStatus, SetupInit, UserOut
from app.auth import hash_password
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


async def create_default_categories(db: AsyncSession):
    """Create default categories and subcategories"""
    categories_data = [
        {
            "code": "algorithms",
            "name_en": "Algorithms & Data Structures",
            "name_es": "Algoritmos y Estructuras de Datos",
            "description_en": "Fundamental algorithms and data structures",
            "description_es": "Algoritmos fundamentales y estructuras de datos",
            "icon": "algorithm",
            "order": 1,
            "range_start": 10,
            "range_end": 99,
            "subcategories": [
                {"code": "basics", "name_en": "Basics", "name_es": "Basicos"},
                {"code": "search", "name_en": "Search", "name_es": "Busqueda"},
                {"code": "greedy", "name_en": "Greedy", "name_es": "Voraces"},
                {"code": "divide-conquer", "name_en": "Divide & Conquer", "name_es": "Divide y Conquista"},
                {"code": "data-structures", "name_en": "Data Structures", "name_es": "Estructuras de Datos"},
                {"code": "graph-theory", "name_en": "Graph Theory", "name_es": "Teoria de Grafos"},
                {"code": "dynamic-programming", "name_en": "Dynamic Programming", "name_es": "Programacion Dinamica"},
                {"code": "strings", "name_en": "Strings", "name_es": "Strings"},
                {"code": "mathematics", "name_en": "Mathematics", "name_es": "Matematicas"},
                {"code": "geometry", "name_en": "Geometry", "name_es": "Geometria"},
                {"code": "network-flow", "name_en": "Network Flow", "name_es": "Flujo en Redes"},
            ]
        },
        {
            "code": "bitcoin-protocol",
            "name_en": "Bitcoin Core & Protocol",
            "name_es": "Bitcoin Core y Protocolo",
            "description_en": "Bitcoin protocol, consensus and node operations",
            "description_es": "Protocolo Bitcoin, consenso y operaciones de nodos",
            "icon": "bitcoin",
            "order": 2,
            "range_start": 100,
            "range_end": 199,
            "subcategories": [
                {"code": "fundamentals", "name_en": "Fundamentals", "name_es": "Fundamentos"},
                {"code": "transactions-script", "name_en": "Transactions & Script", "name_es": "Transacciones y Script"},
                {"code": "blocks-consensus", "name_en": "Blocks & Consensus", "name_es": "Bloques y Consenso"},
                {"code": "mining-difficulty", "name_en": "Mining & Difficulty", "name_es": "Mineria y Dificultad"},
                {"code": "utxo-mempool", "name_en": "UTXO & Mempool", "name_es": "UTXO y Mempool"},
                {"code": "p2p-network", "name_en": "P2P Network", "name_es": "Red P2P"},
                {"code": "storage-indexing", "name_en": "Storage & Indexing", "name_es": "Almacenamiento e Indexacion"},
            ]
        },
        {
            "code": "cryptography",
            "name_en": "Cryptography",
            "name_es": "Criptografia",
            "description_en": "Cryptographic primitives in Bitcoin",
            "description_es": "Primitivas criptograficas en Bitcoin",
            "icon": "lock",
            "order": 3,
            "range_start": 200,
            "range_end": 299,
            "subcategories": [
                {"code": "hash-functions", "name_en": "Hash Functions", "name_es": "Funciones Hash"},
                {"code": "signatures-ecc", "name_en": "Signatures & ECC", "name_es": "Firmas y ECC"},
                {"code": "key-management", "name_en": "Key Management", "name_es": "Gestion de Claves"},
                {"code": "encoding", "name_en": "Encoding", "name_es": "Codificacion"},
            ]
        },
        {
            "code": "layer2-3",
            "name_en": "Layer 2/3 & Sidechains",
            "name_es": "Layer 2/3 y Sidechains",
            "description_en": "Lightning, Cashu, sidechains and off-chain protocols",
            "description_es": "Lightning, Cashu, sidechains y protocolos off-chain",
            "icon": "lightning",
            "order": 4,
            "range_start": 300,
            "range_end": 399,
            "subcategories": [
                {"code": "lightning-fundamentals", "name_en": "Lightning Fundamentals", "name_es": "Fundamentos de Lightning"},
                {"code": "lightning-routing", "name_en": "Lightning Routing", "name_es": "Enrutamiento Lightning"},
                {"code": "lightning-advanced", "name_en": "Lightning Advanced", "name_es": "Lightning Avanzado"},
                {"code": "cashu-protocol", "name_en": "Cashu Protocol", "name_es": "Protocolo Cashu"},
                {"code": "sidechains", "name_en": "Sidechains", "name_es": "Sidechains"},
                {"code": "client-validation", "name_en": "Client Validation", "name_es": "Validacion Cliente"},
                {"code": "statechains", "name_en": "Statechains", "name_es": "Statechains"},
                {"code": "covenants", "name_en": "Covenants", "name_es": "Covenants"},
            ]
        },
        {
            "code": "privacy-security",
            "name_en": "Privacy & Security",
            "name_es": "Privacidad y Seguridad",
            "description_en": "Privacy, chain analysis and security",
            "description_es": "Privacidad, analisis de cadena y seguridad",
            "icon": "shield",
            "order": 5,
            "range_start": 400,
            "range_end": 499,
            "subcategories": [
                {"code": "privacy-techniques", "name_en": "Privacy Techniques", "name_es": "Tecnicas de Privacidad"},
                {"code": "chain-analysis", "name_en": "Chain Analysis", "name_es": "Analisis de Cadena"},
                {"code": "security", "name_en": "Security", "name_es": "Seguridad"},
            ]
        }
    ]

    category_count = 0
    subcategory_count = 0

    for cat_data in categories_data:
        subcats_data = cat_data.pop("subcategories")

        category = Category(
            code=cat_data["code"],
            name_en=cat_data["name_en"],
            name_es=cat_data["name_es"],
            description_en=cat_data["description_en"],
            description_es=cat_data["description_es"],
            icon=cat_data["icon"],
            order=cat_data["order"],
            problem_range_start=cat_data["range_start"],
            problem_range_end=cat_data["range_end"]
        )

        db.add(category)
        await db.flush()
        category_count += 1

        for idx, subcat_data in enumerate(subcats_data, 1):
            subcategory = Subcategory(
                category_id=category.id,
                code=subcat_data["code"],
                name_en=subcat_data["name_en"],
                name_es=subcat_data["name_es"],
                order=idx
            )
            db.add(subcategory)
            subcategory_count += 1

    logger.info(f"Created {category_count} categories and {subcategory_count} subcategories")
    return category_count, subcategory_count


@router.get("/status", response_model=SetupStatus)
async def get_setup_status(db: AsyncSession = Depends(get_db)):
    """
    Check if application needs initial setup

    Returns needs_setup=True if no users exist in database

    **Returns:**
    - needs_setup: True if setup is required, False otherwise
    - message: Descriptive message
    """
    # Count total users
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar()

    needs_setup = user_count == 0

    if needs_setup:
        message = "No users found. Initial setup required."
    else:
        message = "Application is already configured."

    logger.info(f"Setup status checked: needs_setup={needs_setup}, user_count={user_count}")

    return SetupStatus(
        needs_setup=needs_setup,
        message=message
    )


@router.post("/init", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def initialize_setup(
    setup_data: SetupInit,
    db: AsyncSession = Depends(get_db)
):
    """
    Initialize application with first admin user

    This endpoint only works when no users exist.
    Creates the first admin user and genesis block.

    **Request body:**
    - username: Admin username (3-50 chars, alphanumeric + underscore)
    - password: Admin password (min 8 chars)

    **Returns:**
    - User object with admin role

    **Errors:**
    - 400: Setup already completed (users exist)
    - 400: Username validation failed
    """
    # Check if users already exist
    result = await db.execute(select(func.count(User.id)))
    user_count = result.scalar()

    if user_count > 0:
        logger.warning(f"Setup init attempted but {user_count} users already exist")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Setup already completed. Users already exist in the system."
        )

    # Check if username is already taken (shouldn't happen, but just in case)
    result = await db.execute(
        select(User).where(User.username == setup_data.username)
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )

    # Create first admin user
    admin_user = User(
        username=setup_data.username,
        password_hash=hash_password(setup_data.password),
        role=UserRole.ADMIN,
        total_score=0,
        problems_solved=0,
        blocks_mined=0
    )

    db.add(admin_user)
    await db.flush()  # Get ID

    logger.info(f"First admin user created: {admin_user.username} (ID: {admin_user.id})")

    # Create genesis block
    from app.models import Block
    from datetime import datetime

    genesis_block = Block(
        block_height=0,
        block_hash="0" * 64,
        prev_block_hash="0" * 64,
        timestamp=datetime.utcnow(),
        tx_count=0,
        total_points=0,
        block_size=0,
        miner_id=None,
        miner_username="Satoshi Nakamoto",
        is_empty=False,
        # Bitcoin genesis block reference
        btc_block_height=0,
        btc_block_hash="000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
        btc_timestamp=datetime(2009, 1, 3, 18, 15, 5),
        btc_tx_count=1,
        btc_fees=0,
        btc_size=285,
        btc_weight=904,
        btc_miner="Satoshi Nakamoto",
        btc_difficulty=1.0,
    )

    db.add(genesis_block)
    logger.info("Genesis block created (height: 0)")

    # Create default categories and subcategories
    cat_count, subcat_count = await create_default_categories(db)
    logger.info(f"Created {cat_count} categories and {subcat_count} subcategories")

    # Commit transaction
    await db.commit()
    await db.refresh(admin_user)

    logger.info("=" * 60)
    logger.info("Initial setup completed successfully!")
    logger.info(f"   Admin user: {admin_user.username}")
    logger.info(f"   Genesis block: height 0")
    logger.info(f"   Categories: {cat_count}")
    logger.info(f"   Subcategories: {subcat_count}")
    logger.info("=" * 60)

    return admin_user
