# GraphQL utilities for SplatNet3 API
# Based on reference-project/splatoon3-nso/s3s/utils.py
"""GraphQL query hashes and utilities for SplatNet3 API."""

import json
from typing import Optional

# SplatNet3 API endpoints
SPLATNET3_URL = "https://api.lp1.av5ja.srv.nintendo.net"
GRAPHQL_URL = f"{SPLATNET3_URL}/api/graphql"

# SHA256 hash database for SplatNet 3 GraphQL queries (参照 splatoon3-nso)
QUERY_HASHES = {
    'HomeQuery': '51fc56bbf006caf37728914aa8bc0e2c86a80cf195b4d4027d6822a3623098a8',
    'LatestBattleHistoriesQuery': 'b24d22fd6cb251c515c2b90044039698aa27bc1fab15801d83014d919cd45780',
    'RegularBattleHistoriesQuery': '2fe6ea7a2de1d6a888b7bd3dbeb6acc8e3246f055ca39b80c4531bbcd0727bba',
    'BankaraBattleHistoriesQuery': '9863ea4744730743268e2940396e21b891104ed40e2286789f05100b45a0b0fd',
    'PrivateBattleHistoriesQuery': 'fef94f39b9eeac6b2fac4de43bc0442c16a9f2df95f4d367dd8a79d7c5ed5ce7',
    'XBattleHistoriesQuery': 'eb5996a12705c2e94813a62e05c0dc419aad2811b8d49d53e5732290105559cb',
    'VsHistoryDetailQuery': '94faa2ff992222d11ced55e0f349920a82ac50f414ae33c83d1d1c9d8161c5dd',
    'EventBattleHistoriesQuery': 'e47f9aac5599f75c842335ef0ab8f4c640e8bf2afe588a3b1d4b480ee79198ac',
    'CoopHistoryQuery': 'e11a8cf2c3de7348495dea5cdcaa25e0c153541c4ed63f044b6c174bc5b703df',
    'CoopHistoryDetailQuery': 'f2d55873a9281213ae27edc171e2b19131b3021a2ae263757543cdd3bf015cc8',
    'PagerLatestVsDetailQuery': '73462e18d464acfdf7ac36bde08a1859aa2872a90ed0baed69c94864c20de046',
    'FriendListQuery': 'ea1297e9bb8e52404f52d89ac821e1d73b726ceef2fd9cc8d6b38ab253428fb3',
    'HistoryRecordQuery': 'a654ecc80161a7ca5c38761c1d9e502d405eae764e2d343618b9c74b1dc0a80f',
    'TotalQuery': '2a9302bdd09a13f8b344642d4ed483b9464f20889ac17401e993dfa5c2bb3607',
    'XRankingQuery': 'a5331ed228dbf2e904168efe166964e2be2b00460c578eee49fc0bc58b4b899c',
    'XRanking500Query': '90932ee3357eadab30eb11e9d6b4fe52d6b35fde91b5c6fd92ba4d6159ea1cb7',
    'StageScheduleQuery': '9b6b90568f990b2a14f04c25dd6eb53b35cc12ac815db85ececfccee64215edd',
    'StageRecordQuery': 'c8b31c491355b4d889306a22bd9003ac68f8ce31b2d5345017cdd30a2c8056f3',
    'WeaponRecordQuery': '6b8db227bbe479401875e509a95c3183931e708ec222a824f8d4157cebea4584',
    'EventListQuery': 'bf5cefda9fb6a7511fe4620a0be0c7492ca56ae10f41790cf490bbe8904fefea',
    'EventBoardQuery': 'ad4097d5fb900b01f12dffcb02228ef6c20ddbfba41f0158bb91e845335c708e',
    'CatalogQuery': '52c4b6a69b45e9f2c51f5efc6c7c3679bafb8e7d0ff8f31ce53a68b9bd945f9f',
}


def gen_graphql_body(
    query_name: str,
    var_name: Optional[str] = None,
    var_value: Optional[str] = None
) -> str:
    """
    生成 GraphQL 请求体（参照 splatoon3-nso）
    
    Args:
        query_name: 查询名称
        var_name: 可选的变量名
        var_value: 可选的变量值
        
    Returns:
        JSON string for GraphQL request
        
    Raises:
        ValueError: If query_name not found
    """
    if query_name not in QUERY_HASHES:
        raise ValueError(f"Unknown query: {query_name}")
    
    sha256_hash = QUERY_HASHES[query_name]
    variables = {}
    
    if var_name and var_value:
        variables[var_name] = var_value
    
    body = {
        "extensions": {
            "persistedQuery": {
                "sha256Hash": sha256_hash,
                "version": 1
            }
        },
        "variables": variables
    }
    
    return json.dumps(body)
