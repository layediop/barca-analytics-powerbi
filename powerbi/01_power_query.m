// =====================================================================
//  BARÇA ANALYTICS – REQUÊTES POWER QUERY (M)
//  1) Accueil > Transformer les données > Gérer les paramètres > Nouveau paramètre
//       Nom : DossierDonnees   Type : Texte
//       Valeur : chemin du dossier data AVEC la barre finale, ex. C:\BarcaAnalytics\data\
//  2) Pour chaque table : Nouvelle source > Requête vide > Éditeur avancé,
//     coller le code, puis renommer la requête avec le nom indiqué.
//
//  Deux réglages évitent les erreurs classiques :
//   - Encoding = 65001 (UTF-8) : sinon « Iñaki Peña » devient « IÃ±aki PeÃ±a ».
//   - Culture "en-US" dans TransformColumnTypes : les CSV utilisent le point
//     décimal ; avec un Windows en français, « 0.0537 » serait lu comme 537.
// =====================================================================

// ---------------- Requête : DimMatch ----------------
let
    Source  = Csv.Document(
                  File.Contents(DossierDonnees & "DimMatch.csv"),
                  [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
              ),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types   = Table.TransformColumnTypes(
        Entetes,
        {
            {"match_id", Int64.Type},
            {"match_date", type date},
            {"kick_off", type text},
            {"season", type text},
            {"matchweek", Int64.Type},
            {"opponent_id", Int64.Type},
            {"opponent_name", type text},
            {"venue", type text},
            {"stadium", type text},
            {"referee", type text},
            {"barca_manager", type text},
            {"opponent_manager", type text},
            {"goals_for", Int64.Type},
            {"goals_against", Int64.Type},
            {"result", type text},
            {"points", Int64.Type},
            {"score_label", type text},
            {"result_code", type text},
            {"match_label", type text}
        },
        "en-US"
    )
in
    Types

// ---------------- Requête : DimTeam ----------------
let
    Source  = Csv.Document(
                  File.Contents(DossierDonnees & "DimTeam.csv"),
                  [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
              ),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types   = Table.TransformColumnTypes(
        Entetes,
        {
            {"team_id", Int64.Type},
            {"team_name", type text},
            {"is_barca", Int64.Type},
            {"team_side", type text}
        },
        "en-US"
    )
in
    Types

// ---------------- Requête : DimPlayer ----------------
let
    Source  = Csv.Document(
                  File.Contents(DossierDonnees & "DimPlayer.csv"),
                  [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
              ),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types   = Table.TransformColumnTypes(
        Entetes,
        {
            {"player_id", Int64.Type},
            {"player_name", type text},
            {"full_name", type text},
            {"country", type text},
            {"main_position", type text},
            {"position_group", type text},
            {"is_barca_player", Int64.Type}
        },
        "en-US"
    )
in
    Types

// ---------------- Requête : FactShots ----------------
let
    Source  = Csv.Document(
                  File.Contents(DossierDonnees & "FactShots.csv"),
                  [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
              ),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types   = Table.TransformColumnTypes(
        Entetes,
        {
            {"shot_id", type text},
            {"match_id", Int64.Type},
            {"team_id", Int64.Type},
            {"player_id", Int64.Type},
            {"assist_player_id", Int64.Type},
            {"period", Int64.Type},
            {"minute", Int64.Type},
            {"second", Int64.Type},
            {"minute_bucket", type text},
            {"xg", type number},
            {"outcome", type text},
            {"shot_result", type text},
            {"is_goal", Int64.Type},
            {"is_on_target", Int64.Type},
            {"is_penalty", Int64.Type},
            {"shot_type", type text},
            {"body_part", type text},
            {"technique", type text},
            {"play_pattern", type text},
            {"under_pressure", Int64.Type},
            {"first_time", Int64.Type},
            {"x", type number},
            {"y", type number},
            {"map_x", type number},
            {"map_y", type number},
            {"distance_m", type number},
            {"zone", type text}
        },
        "en-US"
    )
in
    Types

// ---------------- Requête : FactPlayerMatch ----------------
let
    Source  = Csv.Document(
                  File.Contents(DossierDonnees & "FactPlayerMatch.csv"),
                  [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
              ),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types   = Table.TransformColumnTypes(
        Entetes,
        {
            {"match_id", Int64.Type},
            {"player_id", Int64.Type},
            {"team_id", Int64.Type},
            {"is_starter", Int64.Type},
            {"position", type text},
            {"position_group", type text},
            {"minutes", type number},
            {"yellow_cards", Int64.Type},
            {"red_cards", Int64.Type},
            {"goals", Int64.Type},
            {"non_penalty_goals", Int64.Type},
            {"shots", Int64.Type},
            {"shots_on_target", Int64.Type},
            {"xg", type number},
            {"npxg", type number},
            {"assists", Int64.Type},
            {"xa", type number},
            {"key_passes", Int64.Type},
            {"passes", Int64.Type},
            {"passes_completed", Int64.Type},
            {"progressive_passes", Int64.Type},
            {"passes_into_box", Int64.Type},
            {"crosses", Int64.Type},
            {"dribbles", Int64.Type},
            {"dribbles_completed", Int64.Type},
            {"progressive_carries", Int64.Type},
            {"tackles", Int64.Type},
            {"tackles_won", Int64.Type},
            {"interceptions", Int64.Type},
            {"ball_recoveries", Int64.Type},
            {"pressures", Int64.Type},
            {"fouls_committed", Int64.Type},
            {"fouls_won", Int64.Type},
            {"touches", Int64.Type}
        },
        "en-US"
    )
in
    Types

// ---------------- Requête : FactTeamMatch ----------------
let
    Source  = Csv.Document(
                  File.Contents(DossierDonnees & "FactTeamMatch.csv"),
                  [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
              ),
    Entetes = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Types   = Table.TransformColumnTypes(
        Entetes,
        {
            {"match_id", Int64.Type},
            {"team_id", Int64.Type},
            {"is_barca", Int64.Type},
            {"goals", Int64.Type},
            {"possession_pct", type number},
            {"shots", Int64.Type},
            {"shots_on_target", Int64.Type},
            {"xg", type number},
            {"passes", Int64.Type},
            {"passes_completed", Int64.Type}
        },
        "en-US"
    )
in
    Types
