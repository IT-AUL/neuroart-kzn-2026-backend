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
        "models": [
            {
                "id": "log_and_wedge",
                "name": "Бревно с трещиной и клином",
                "url": "models/loc1_log_shurale.glb",
                "is_primary": True,
            },
            {
                "id": "shurale",
                "name": "Шурале",
                "url": "models/loc1_shurale_char.glb",
                "is_primary": False,
            },
            {
                "id": "cart",
                "name": "Телега дровосека",
                "url": "models/loc1_cart.glb",
                "is_primary": False,
            },
        ],
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
            "layer2": "Поэма «Шурале» Габдуллы Тукая написана в 1907 году, действие происходит в деревне Кырлай, где прошло детство самого поэта. По ее сюжету в 1939 году композитор Фарид Яруллин начал писать музыку первого татарского балета, но погиб на фронте в 1943 году и не увидел постановки. Премьера балета «Шурале» состоялась 12 марта 1945 года в Казани, в Татарском театре оперы и балета. В 2011 году у театра Камала в Казани установили бронзовую скульптуру «Загадки Шурале»: Шурале и дровосек сидят вместе на бревне, а на самом бревне выгравирована пословица «где сила не может, там ум поможет».",
            "action_hint": "Веди пальцем по щели бревна, затем тапни по клину для удара топором",
            "dialogue": [
                {
                    "speaker": "Дровосек",
                    "text": "Давай сперва вместе последнее бревно на телегу закинем, а потом уже поиграем!",
                    "trigger": "shurale_appear",
                },
                {
                    "speaker": "Дровосек",
                    "text": "Где сила не может, там ум поможет. Бывай, лесной хозяин!",
                    "trigger": "shurale_trapped",
                },
            ],
            "easter_egg": "Шутка про имя 'Вгодуминувшем' (Былтыр): когда Шурале зовет на помощь сородичей с криками 'Вгодуминувшем прищемил!', те решают, что беда случилась еще в прошлом году, и не спешат на выручку.",
        },
        "artifact": {"id": "klin", "name": "Клин", "icon": "icons/klin.png"},
        "next_location_id": "loc_2_sabantuy",
        "next_location_order": 2,
        "next_location_hint": "Отправляйтесь на майдан на праздник Сабантуй к столбу с призом",
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
            "grace_period_seconds": 1.0,
            "success_threshold": 100,
        },
        "marker": {"type": "image", "asset": "marker_pole.png"},
        "model_url": "models/loc2_pole_climber.glb",
        "models": [
            {
                "id": "pole_and_towel",
                "name": "Столб с призовым полотенцем",
                "url": "models/loc2_pole_climber.glb",
                "is_primary": True,
            },
            {
                "id": "climber",
                "name": "Человечек-скалолаз",
                "url": "models/loc2_climber_char.glb",
                "is_primary": False,
            },
        ],
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
            "action_hint": "Лезь наверх, тапай часто, иначе соскользнешь! При паузе больше 1 секунды сползешь вниз.",
            "dialogue": [
                {
                    "speaker": "Ведущий майдана",
                    "text": "Айда, батыр, лезь за призом! Полотенце ждет на самой верхушке!",
                    "trigger": "start",
                }
            ],
            "easter_egg": "ЗАПОЛНИТЬ!!!!",
        },
        "artifact": {
            "id": "polotentse",
            "name": "Полотенце",
            "icon": "icons/polotentse.png",
        },
        "next_location_id": "loc_3_chak_chak",
        "next_location_order": 3,
        "next_location_hint": "Загляните на праздничное чаепитие во дворе и угоститесь чак-чаком",
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
        "models": [
            {
                "id": "table_samovar",
                "name": "Стол с самоваром",
                "url": "models/loc3_table_samovar.glb",
                "is_primary": True,
            },
            {
                "id": "chak_chak",
                "name": "Блюдо чак-чака",
                "url": "models/loc3_chak_chak_dish.glb",
                "is_primary": False,
            },
            {
                "id": "cups",
                "name": "Чайные чашки",
                "url": "models/loc3_cups.glb",
                "is_primary": False,
            },
        ],
        "coordinates": {"x": 0, "y": 0, "z": 0, "scale": 1.0},
        "animations": [
            {"id": 0, "name": "samovar_steam_loop"},
            {"id": 1, "name": "cup_fill"},
        ],
        "texts": {
            "layer1": "Чак-чак как обязательное угощение на Сабантуе и главный символ татарского гостеприимства.",
            "layer2": "ЗАПОЛНИТЬ!!!!",
            "action_hint": "Здесь можно просто отдохнуть с дороги. Тапните по чак-чаку, чтобы положить угощение в альбом.",
            "dialogue": [
                {
                    "speaker": "Хозяйка",
                    "text": "Рәхим итегез! Угощайтесь чак-чаком и горячим чаем с дороги!",
                    "trigger": "enter",
                }
            ],
            "easter_egg": "ЗАПОЛНИТЬ!!!!",
        },
        "artifact": {
            "id": "chak_chak",
            "name": "Чак-чак",
            "icon": "icons/chak_chak.png",
        },
        "next_location_id": None,
        "next_location_order": None,
        "next_location_hint": "Поздравляем! Демо-маршрут завершен. Откройте экран альбома, чтобы увидеть собранные награды!",
    },
]
