from typing import Any, Dict, List

INITIAL_LOCATIONS: List[Dict[str, Any]] = [
    {
        "id": "loc_1_shurale",
        "order": 1,
        "priority": "P0",
        "title": "Дровосек-батыр и Шурале",
        "mechanic": "trace",
        "mechanic_params": {
            "path": "заполняет 3D-художник после экспорта модели бревна",
            "tolerance": 20,
        },
        "marker": {"type": "image", "asset": "marker_log.png"},
        "model_url": "models/loc1_log_shurale.glb",
        "coordinates": {"x": 0, "y": 0, "z": 0, "scale": 1.0},
        "animations": [
            {"id": 0, "name": "log_idle_crack_closed"},
            {"id": 1, "name": "log_crack_open"},
            {"id": 2, "name": "shurale_appear_threat"},
            {"id": 3, "name": "shurale_idle"},
            {"id": 4, "name": "shurale_insert_fingers"},
            {"id": 5, "name": "wedge_hit"},
            {"id": 6, "name": "shurale_trapped"},
            {"id": 7, "name": "shurale_calls_for_help"},
        ],
        "texts": {
            "layer1": "Одиночная работа в лесу была по-настоящему опасной, ценились смелость и смекалка.",
            "layer2": "Поэма «Шурале» Габдуллы Тукая написана в 1907 году, действие происходит в деревне Кырлай, где прошло детство самого поэта. По ее сюжету в 1939 году композитор Фарид Яруллин начал писать музыку первого татарского балета, но погиб на фронте в 1943 году и не увидел постановки. Премьера балета «Шурале» состоялась 12 марта 1945 года в Казани, в Татарском театре оперы и балета. В 2011 году у театра Камала в Казани установили бронзовую скульптуру «Загадки Шурале»: Шурале и дровосек сидят вместе на бревне, а на самом бревне выгравирована пословица «где сила не может, там ум поможет». Отдельная пасхалка по тапу на реплику: шутка про имя Вгодуминувшем, когда Шурале зовет на помощь сородичей, те решают что его прищемило еще в прошлом году, и не спешат бежать.",
        },
        "artifact": {"id": "klin", "name": "Клин", "icon": "icons/klin.png"},
    },
    {
        "id": "loc_2_sabantuy",
        "order": 2,
        "priority": "P1",
        "title": "Сабантуй, лазание на столб",
        "mechanic": "tap_climb",
        "mechanic_params": {
            "gain_per_tap": 4,
            "decay_per_interval": 1,
            "decay_interval_seconds": 0.3,
            "success_threshold": 100,
        },
        "marker": {"type": "image", "asset": "marker_pole.png"},
        "model_url": "models/loc2_pole_climber.glb",
        "coordinates": {"x": 0, "y": 0, "z": 0, "scale": 1.0},
        "animations": [
            {"id": 0, "name": "climber_idle_base"},
            {"id": 1, "name": "climbing_loop"},
            {"id": 2, "name": "slip_down"},
            {"id": 3, "name": "victory_grab_prize"},
        ],
        "texts": {
            "layer1": "Сабантуй, праздник плуга, отмечает конец весеннего сева, один из главных праздников у татар и башкир.",
            "layer2": "Помимо столба на Сабантуе есть борьба курэш, соперники цепляют полотенца за пояс друг другу, приз победителю исторически живой баран, также бег с ложкой и яйцом и разбивание горшка с закрытыми глазами.",
        },
        "artifact": {
            "id": "polotentse",
            "name": "Полотенце",
            "icon": "icons/polotentse.png",
        },
    },
    {
        "id": "loc_3_chak_chak",
        "order": 3,
        "priority": "P2",
        "title": "Чаепитие и чак-чак",
        "mechanic": "none",
        "mechanic_params": {},
        "marker": {"type": "image", "asset": "marker_table.png"},
        "model_url": "models/loc3_table_samovar.glb",
        "coordinates": {"x": 0, "y": 0, "z": 0, "scale": 1.0},
        "animations": [
            {"id": 0, "name": "samovar_steam_loop"},
            {"id": 1, "name": "cup_fill"},
        ],
        "texts": {
            "layer1": "Чак-чак как обязательное угощение на Сабантуе и главный символ татарского гостеприимства.",
            "layer2": "",
        },
        "artifact": {
            "id": "chak_chak",
            "name": "Чак-чак",
            "icon": "icons/chak_chak.png",
        },
    },
]
