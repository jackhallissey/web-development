// 'root' and 'logged_in' are declared in 'play.html'

let canvas;
let context;
let main_nav_element;
let sidebar_element;
let welcome_element;
let start_element;
let score_element;
let level_element;
let inventory_element;
let power_ups_element;
let message_element;
let clear_message;
let results_list_element;
let results_nav_element;
let clear_results_element;
let player_stats_element;

let paused;
const fps_interval = 1000 / 30;
let then = Date.now();
let request_id;

const levels = [
    {no_enemies : 1, no_treasures : 1, no_walls : 1, enemy_speed : 1, sprite_set : 0},     // Level 1
    {no_enemies : 2, no_treasures : 1, no_walls : 2, enemy_speed : 1, sprite_set : 1},
    {no_enemies : 2, no_treasures : 2, no_walls : 2, enemy_speed : 1, sprite_set : 2},
    {no_enemies : 2, no_treasures : 2, no_walls : 3, enemy_speed : 1, sprite_set : 2},
    {no_enemies : 2, no_treasures : 3, no_walls : 3, enemy_speed : 2, sprite_set : 3},
    {no_enemies : 3, no_treasures : 3, no_walls : 3, enemy_speed : 2, sprite_set : 3}
];

const items = [
    {name : "Gun", type : "weapon"},
    {name : "Shield", type : "defence"}
];

const buffs = {
    "enemies" : "Enemies Frozen",
    "walls" : "Move Through Walls"
}

const sprites = {
    player : [4, 2],
    treasure : [43, 45],
    finish : [20, 42],
    blast : [9, 43]
}

const sprite_sets = [
    {background : [55, 14], walls : [44, 18], border : [8, 16], enemies : [ [1, 3] ]},
    {background : [14, 13], walls : [44, 18], border : [42, 17], enemies : [ [1, 3], [3, 3] ]},
    {background : [44, 13], walls : [44, 18], border : [42, 17], enemies : [ [1, 3], [3, 3] ]},
    {background : [12, 17], walls : [44, 18], border : [35, 14], enemies : [ [0, 5], [9, 5], [12, 5] ]}
];

const finish = {
    size : 15
}

let player = {
    height : 20,
    width : 20,
    x_change : 10,
    y_change : 10
}

const a = Math.abs;

const tile_size = 32;
let tileset = new Image();
let item_sprites = {};
for (let i of items) {
    item_sprites[i.name] = new Image();
}
let power_up_sprites = {};
for (let b of Object.keys(buffs)) {
    power_up_sprites[b] = new Image();
}
let sounds = {
    music : new Audio(),
    footstep : new Audio(),
    treasure : new Audio(),
    win : new Audio(),
    death1 : new Audio(),
    death2 : new Audio(),
    blast : new Audio()
};


let inventory;
let level;
let sprite_set;
let walls;
let enemies;
let treasures;
let blasts;
let score;

let cheats = {};
let cheats_used;
let power_ups = {};
let power_up_decrement = {
    active : false
};

let move_left;
let move_right;
let move_up;
let move_down;

// From the following page: https://stackoverflow.com/questions/8916620/disable-arrow-key-scrolling-in-users-browser
window.addEventListener("keydown", function(e) {
    if(["Space", "ArrowUp", "ArrowDown"].indexOf(e.code) > -1) {
        e.preventDefault();
    }
}, false);

document.addEventListener("DOMContentLoaded", init, false);

function init() {
    canvas = document.querySelector("canvas");
    context = canvas.getContext("2d");
    main_nav_element = document.querySelector("#main_links");
    sidebar_element = document.querySelector("#sidebar");
    welcome_element = document.querySelector("#welcome");
    start_element = document.querySelector("#start");
    score_element = document.querySelector("#score");
    level_element = document.querySelector("#level");
    inventory_element = document.querySelector("#inventory");
    power_ups_element = document.querySelector("#power_ups");
    message_element = document.querySelector("#message");
    results_list_element = document.querySelector("#results_list");
    results_nav_element = document.querySelector("#results_links");
    clear_results_element = document.querySelector("#clear_results");
    clear_results_element.addEventListener("click", clearResults, false);
    player_stats_element = document.querySelector("#player_stats");

    finish.x = canvas.width - finish.size;
    finish.y = canvas.height - finish.size;

    loadAssets(
        {"var" : tileset, "url" : "static/tileset.png"},
        {"var" : item_sprites.Gun, "url" : "static/items/gun.png"},
        {"var" : item_sprites.Shield, "url" : "static/items/shield.png"},
        {"var" : power_up_sprites.enemies, "url" : "static/power_ups/enemies.png"},
        {"var" : power_up_sprites.walls, "url" : "static/power_ups/walls.png"},
        {"var" : sounds.music, "url" : "static/sounds/music.mp3"},
        {"var" : sounds.footstep, "url" : "static/sounds/footstep.ogg"},
        {"var" : sounds.treasure, "url" : "static/sounds/treasure.ogg"},
        {"var" : sounds.win, "url" : "static/sounds/win.ogg"},
        {"var" : sounds.death1, "url" : "static/sounds/death1.ogg"},
        {"var" : sounds.death2, "url" : "static/sounds/death2.ogg"},
        {"var" : sounds.blast, "url" : "static/sounds/blast.ogg"}
    );
}

function loadAssets() {
    let num_assets = arguments.length;
    let loaded = function() {
        console.log("loaded");
        num_assets = num_assets - 1;
        if (num_assets === 0) {
            // Game ready to start
            welcome_element.innerHTML = "Welcome";
            start_element.innerHTML = "Press any key to start the game.";
            window.addEventListener("keydown", startGame, false);
        }
    };
    for (let asset of arguments) {
        let element = asset.var;
        if ( element instanceof HTMLImageElement ) {
            console.log("img");
            element.addEventListener("load", loaded, { once: true });
        }
        else if ( element instanceof HTMLAudioElement ) {
            console.log("audio");
            element.addEventListener("canplaythrough", loaded, { once: true });
        }
        element.src = asset.url;
    }
}

function startGame() {
    if (navigator.userActivation.hasBeenActive) {       // Prevents autoplay error if certain keys are pressed
        window.removeEventListener("keydown", startGame, false);

        sounds.music.currentTime = 0;
        sounds.music.play();
        cheats_used = false;
        level = 0;
        score = 0;
        inventory = {};
        main_nav_element.className = "hidden";
        results_nav_element.className = "hidden";
        sidebar_element.classList.remove("hidden");
        score_element.innerHTML = "Your Score: " + score;
        inventory_element.innerHTML = "";
        power_ups_element.innerHTML = "";

        startLevel();
    }
}

function startLevel() {
    window.removeEventListener("keydown", startLevel, false);

    level += 1;

    move_left = false;
    move_right = false;
    move_up = false;
    move_down = false;
    paused = false;

    power_ups_element.innerHTML = "";

    for (let b of Object.keys(buffs)) {
        cheats[b] = false;
        power_ups[b] = 0;
    }

    window.addEventListener("keydown", activate, false);
    window.addEventListener("keyup", deactivate, false);
    window.addEventListener("keydown", pause, false);
    window.removeEventListener("keydown", resume, false);

    level_element.innerHTML = "Level: " + level;
    welcome_element.innerHTML = "";
    start_element.innerHTML = "";
    message_element.innerHTML = "";

    player.x = 30;
    player.y = 30;

    enemies = [];
    treasures = [];
    walls = [];
    blasts = [];

    let level_data = levels[level-1];
    sprite_set = sprite_sets[level_data.sprite_set];

    let wall_region = 60;
    for (let w = 0; w < level_data.no_walls; w += 1) {
        let wall = {
            y : randIntFactor(wall_region, wall_region + 40, 10),
            size : 10,     // height of wall and width of individual tile in wall
            gap_x : randIntFactor(40, canvas.width - 40, 10),
            gap_width : 40
        }
        walls.push(wall);
        wall_region += 70;
    }

    for (let e = 0; e < level_data.no_enemies; e += 1) {
        let enemy = {
            killed : false,
            size : 20,
            x: randInt(0, canvas.width - 10),
            y: randInt(60, canvas.height - 60),
            x_change: level_data.enemy_speed,
            y_change: level_data.enemy_speed,
            direction : "left",
            sprite : sprite_set.enemies[randInt(0, sprite_set.enemies.length - 1)]
        }
        enemies.push(enemy);
    }

    // Create treasures based on the positions of the walls
    for (let t = 0; t < level_data.no_treasures && t < walls.length; t += 1) {  
        let treasure = {
            found: false,
            size : 20,
            x : randInt(30, canvas.width - 30)
        }
        if (t < walls.length - 1) {
            treasure.y = randInt(walls[t].y + walls[t].size, walls[t+1].y - treasure.size);
        } else {
            treasure.y = randInt(walls[t].y + walls[t].size, canvas.height - treasure.size);
        }
        treasures.push(treasure);
    }

    draw();
}

function draw() {
    request_id = window.requestAnimationFrame(draw);
    if (paused) {
        return;
    }
    let now = Date.now();
    let elapsed = now - then;
    if (elapsed <= fps_interval) {
        return;
    }
    then = now - (elapsed % fps_interval);
    
    context.clearRect(0, 0, canvas.width, canvas.height);

    for (let x = tile_size; x < canvas.width - tile_size; x += tile_size) {
        for (let y = tile_size; y < canvas.height - tile_size; y += tile_size) {
            context.drawImage(tileset, sprite_set.background[0] * tile_size, sprite_set.background[1] * tile_size, tile_size, tile_size, x, y, tile_size, tile_size);
        }
    }

    for (let x = tile_size; x < canvas.width - tile_size; x += tile_size) {
        context.drawImage(tileset, sprite_set.border[0] * tile_size, sprite_set.border[1] * tile_size, tile_size, tile_size, x, 0, tile_size, tile_size);
        context.drawImage(tileset, sprite_set.border[0] * tile_size, sprite_set.border[1] * tile_size, tile_size, tile_size, x, canvas.height - tile_size, tile_size, tile_size);
    }
    for (let y = 0; y < canvas.height; y += tile_size) {
        context.drawImage(tileset, sprite_set.border[0] * tile_size, sprite_set.border[1] * tile_size, tile_size, tile_size, 0, y, tile_size, tile_size);
        context.drawImage(tileset, sprite_set.border[0] * tile_size, sprite_set.border[1] * tile_size, tile_size, tile_size, canvas.width - tile_size, y, tile_size, tile_size);
    }

    for (let w of walls) {
        for (let x = 0; x < w.gap_x; x += w.size) {
            context.drawImage(tileset, sprite_set.walls[0] * tile_size, sprite_set.walls[1] * tile_size, tile_size, tile_size, x, w.y, w.size, w.size);
        }
        for (let x = w.gap_x + w.gap_width; x < canvas.width; x += w.size) {
            context.drawImage(tileset, sprite_set.walls[0] * tile_size, sprite_set.walls[1] * tile_size, tile_size, tile_size, x, w.y, w.size, w.size);
        }
    }

    context.drawImage(tileset, sprites.player[0] * tile_size, sprites.player[1] * tile_size, tile_size, tile_size, player.x, player.y, player.width, player.height);

    context.drawImage(tileset, sprites.finish[0] * tile_size, sprites.finish[1] * tile_size, tile_size, tile_size, finish.x, finish.y, finish.size, finish.size);

    if (playerCollides(finish)) {
        win();
        return;
    }

    for (let t of treasures) {
        if (!(t.found)) {
            context.drawImage(tileset, sprites.treasure[0] * tile_size, sprites.treasure[1] * tile_size, tile_size, tile_size, t.x, t.y, t.size, t.size);
            if (playerCollides(t)) {
                score += 10;
                score_element.innerHTML = "Your Score: " + score;
                t.found = true;
                sounds.treasure.play();
                // Chance of gaining a power-up or item
                let rand = Math.random();
                if (rand < 0.2) {
                    // Gain power-up
                    let b_keys = Object.keys(buffs)
                    let b = b_keys[randInt(0, b_keys.length - 1)];
                    power_ups[b] += 5;
                    updatePowerUps();
                    display("Gained Power-up: " + buffs[b]);
                    if (!(power_up_decrement.active)) {
                        power_up_decrement.active = true;
                        power_up_decrement.timeout = setTimeout(decrementPowerUps, 1000);
                    }
                } else if (rand < 0.6) {
                    // Gain inventory item
                    let item_id = randInt(0, items.length - 1);
                    if (inventory.hasOwnProperty(item_id)) {
                        inventory[item_id] += 1;
                    } else {
                        inventory[item_id] = 1;
                    }
                    updateInventory();
                    display("Gained " + items[item_id].name);
                } else {
                    display("No item gained");
                }
            }
        }
    }

    for (let e of enemies) {
        if (!(e.killed)) {
            if (e.direction === "left") {
                context.drawImage(tileset, e.sprite[0] * tile_size, e.sprite[1] * tile_size, tile_size, tile_size, e.x, e.y, e.size, e.size);
            } else {
                context.drawImage(tileset, (e.sprite[0] + 1) * tile_size, e.sprite[1] * tile_size, tile_size, tile_size, e.x, e.y, e.size, e.size);
            }
            if (playerCollides(e)) {
                let has_defence = false;
                for (let item_id of Object.keys(inventory)) {
                    if (items[item_id].type === "defence" && inventory[item_id] > 0) {
                        has_defence = true;
                        e.killed = true;
                        sounds.death2.play();
                        display("Used " + items[item_id].name);
                        inventory[item_id] -= 1;
                        updateInventory();
                        break;
                    }
                }
                if (!(has_defence)) {
                    lose();
                    return;
                }
            }
        }
    }

    for (let b of blasts) {
        if (!(b.used)) {
            context.drawImage(tileset, sprites.blast[0] * tile_size, sprites.blast[1] * tile_size, tile_size, tile_size, b.x, b.y, b.size, b.size);
            b.x += b.x_change;
            if (b.x <= 0 || b.x + b.size >= canvas.width) {
                b.used = true;
            }
            for (let e of enemies) {
                if (!(e.killed) &&
                    b.x + b.size >= e.x &&
                    e.x + e.size >= b.x &&
                    b.y <= e.y + e.size &&
                    e.y <= b.y + b.size) {
                    b.used = true;
                    e.killed = true;
                    sounds.death2.play();
                    break;
                }
            }
        }
    }

    if (move_left) {
        let valid_move = true;
        if (player.x <= 0) {
            valid_move = false;
        } else if (!(cheats.walls || power_ups.walls > 0)) {
            for (let w of walls) {
                if ((player.y + player.height > w.y && player.y < w.y + w.size) &&
                    (player.x <= w.gap_x)) {
                    valid_move = false;
                    break;
                }
            }
        }
        if (valid_move) {
            player.x = player.x - player.x_change;
            sounds.footstep.play();
        }
    } else if (move_right) {
        let valid_move = true;
        if (player.x + player.width >= canvas.width) {
            valid_move = false;
        } else if (!(cheats.walls || power_ups.walls > 0)) {
            for (let w of walls) {
                if ((player.y + player.height > w.y && player.y < w.y + w.size) &&
                    (w.gap_x + w.gap_width <= player.x + player.width)) {
                    valid_move = false;
                    break;
                }
            }
        }
        if (valid_move) {
            player.x = player.x + player.x_change;
            sounds.footstep.play();
        }
    } else if (move_up) {
        let valid_move = true;
        if (player.y <= 0) {
            valid_move = false;
        } else if (!(cheats.walls || power_ups.walls > 0)) {
            for (let w of walls) {
                if ((player.y > w.y) &&
                    (w.y <= player.y + player.height &&
                    player.y <= w.y + w.size) &&
                    (player.x < w.gap_x ||
                    w.gap_x + w.gap_width < player.x + player.width)) {
                    valid_move = false;
                    break;
                }
            }
        }
        if (valid_move) {
            player.y = player.y - player.y_change;
            sounds.footstep.play();
        }
    } else if (move_down) {
        let valid_move = true;
        if (player.y + player.height >= canvas.height) {
            valid_move = false;
        } else if (!(cheats.walls || power_ups.walls > 0)) {
            for (let w of walls) {
                if ((player.y < w.y) &&
                    (w.y <= player.y + player.height &&
                    player.y <= w.y + w.size) &&
                    (player.x < w.gap_x ||
                    w.gap_x + w.gap_width < player.x + player.width)) {
                    valid_move = false;
                    break;
                }
            }
        }
        if (valid_move) {
            player.y = player.y + player.y_change;
            sounds.footstep.play();
        }
    }

    if (!(cheats.enemies || power_ups.enemies > 0)) {
        for (let e of enemies) {
            if (!(e.killed)) {
                if (e.x > player.x && e.x > 0 &&
                    a(player.x - e.x) > a(player.x - e.x + e.x_change)) {    // Only move if distance between enemy and player would be reduced (prevents enemy from bouncing back and forth)
                    e.x = e.x - e.x_change;
                    e.direction = "left";
                } else if (e.x < player.x && e.x + e.size < canvas.width &&
                           a(player.x - e.x) > a(player.x - e.x - e.x_change)) {
                    e.x = e.x + e.x_change;
                    e.direction = "right";
                }

                if (e.y > player.y && e.y > 0 && 
                    a(player.y - e.y) > a(player.y - e.y + e.y_change)) {
                    e.y = e.y - e.y_change;
                } else if (e.y < player.y && e.y + e.size < canvas.height && 
                           a(player.y - e.y) > a(player.y - e.y - e.y_change)) {
                    e.y = e.y + e.y_change;
                }
            }
        }
    }
}

function activate(event) {
    let key = event.key;
    if (!(paused)) {
        // Move player
        if (key === "ArrowLeft") {
            move_left = true;
        } else if (key === "ArrowRight") {
            move_right = true;
        } else if (key === "ArrowUp") {
            move_up = true;
        } else if (key === "ArrowDown") {
            move_down = true;
        // Shoot
        } else if (key === "a" || key === "A" || key === "d" || key === "D") {
            for (let item_id of Object.keys(inventory)) {
                if (items[item_id].type === "weapon" && inventory[item_id] > 0) {
                    display("Used " + items[item_id].name);
                    inventory[item_id] -= 1;
                    updateInventory();
                    let blast = {
                        used : false,
                        x : player.x,
                        y : player.y,
                        size : 7
                    }
                    if (key === "a" || key === "A") {
                        blast.x_change = -5;
                    } else {
                        blast.x_change = 5;
                    }
                    blasts.push(blast);
                    sounds.blast.play();
                    break;
                }
            }
        }
    }
    // Toggle cheats
    if (key === "`") {
        cheats.enemies = !(cheats.enemies);
    } else if (key === "#") {
        cheats.walls = !(cheats.walls);
    }
    if (!(cheats_used)) {
        for (let b of Object.keys(buffs)) {
            if (cheats[b]) {
                cheats_used = true;
                break;
            }
        }
    }
}

function deactivate(event) {
    let key = event.key;
    if (key === "ArrowLeft") {
        move_left = false;
    } else if (key === "ArrowRight") {
        move_right = false;
    } else if (key === "ArrowUp") {
        move_up = false;
    } else if (key === "ArrowDown") {
        move_down = false;
    }
}

function playerCollides(o) {
    if (player.x + player.width < o.x ||
        o.x + o.size < player.x ||
        player.y > o.y + o.size ||
        o.y > player.y + player.height) {
        return false;
    } else {
        return true;
    }
}

function updateInventory() {
    let contents = "";
    for (let item_id of Object.keys(inventory)) {
        let amount = inventory[item_id];
        if (amount > 0) {
            let name = items[item_id].name;
            let sprite = item_sprites[name].src;
            contents += `<tr><td><img src="${sprite}" alt="" height="24" width="24"></td><td>${name}</td><td>${amount}</td></tr>`;
        }
    }
    inventory_element.innerHTML = contents;
}

function updatePowerUps() {
    let contents = "";
    for (let b of Object.keys(buffs)) {
        let time = power_ups[b];
        if (time > 0) {
            let sprite = power_up_sprites[b].src;
            contents += `<tr><td><img src="${sprite}" alt="" height="24" width="24"></td><td>${buffs[b]}</td><td>${time}</td></tr>`;
        }
    }
    power_ups_element.innerHTML = contents;
}

function decrementPowerUps() {
    if (paused || !(power_up_decrement.active)) {
        return;
    }
    let remaining = false;
    for (let b of Object.keys(buffs)) {
        if (power_ups[b] > 0) {
            remaining = true;
            power_ups[b] -= 1;
        }
    }
    updatePowerUps();
    if (remaining) {
        power_up_decrement.timeout = setTimeout(decrementPowerUps, 1000);
    } else {
        power_up_decrement.active = false;
    }
}

function display(message) {
    clearTimeout(clear_message);
    message_element.innerHTML = message;
    clear_message = setTimeout(() => {
        message_element.innerHTML = "";
    }, 2000);
}

function lose() {
    endLevel();
    endGame();
    sounds.death1.play();
    welcome_element.innerHTML = "You lose!";
    start_element.innerHTML = "Press any key to restart the game.";
}

function win() {
    endLevel();
    sounds.win.play();
    if (level === levels.length) {
        level += 1;     // Completed final level
        endGame();
        welcome_element.innerHTML = "You have completed the game!";
        start_element.innerHTML = "Press any key to restart the game.";
    } else {
        window.addEventListener("keydown", startLevel, false);
        welcome_element.innerHTML = "You win!";
        start_element.innerHTML = "Press any key to advance to the next level.";
    }
}

function endLevel() {
    window.cancelAnimationFrame(request_id);
    window.removeEventListener("keydown", activate, false);
    window.removeEventListener("keyup", deactivate, false);
    window.removeEventListener("keydown", pause, false);
    window.removeEventListener("keydown", resume, false);
    message_element.innerHTML = "";
    clearTimeout(power_up_decrement.timeout);
    power_up_decrement.active = false;
}

function endGame() {
    window.addEventListener("keydown", startGame, false);

    sounds.music.pause();
    main_nav_element.classList.remove("hidden");
    results_nav_element.classList.remove("hidden");
    clear_results_element.classList.remove("hidden");
    
    let handleResponse = function() {
        if (store_result_request.readyState === 4) {
            if (store_result_request.status === 200 && store_result_request.responseText === "success") {
                console.log("Store result - success");
                updateStats();
            } else {
                console.log("Store result - failed");
            }
        }
    }

    let data = new FormData();
    data.append("score", score);
    data.append("levels", level - 1);     // Number of levels completed (not just reached)
    data.append("cheats", cheats_used);

    let store_result_request = new XMLHttpRequest();
    store_result_request.addEventListener("readystatechange", handleResponse, false);
    store_result_request.open("POST", root + "/store_result", true);
    store_result_request.send(data);
}

function updateStats() {
    let handleResponse = function() {
        if (stats_request.readyState === 4) {
            if (stats_request.status === 200) {
                console.log("Stats - success");
                let response = stats_request.responseText.split("<!-- Stats -->");
                results_list_element.innerHTML = response[0];
                if (logged_in) {
                    player_stats_element.innerHTML = response[1];
                }
            } else {
                console.log("Stats - failed");
            }
        }
    }

    let stats_request = new XMLHttpRequest();
    stats_request.addEventListener("readystatechange", handleResponse, false);
    stats_request.open("GET", root + "/stats", true);
    stats_request.send();
}

function clearResults() {
    let handleResponse = function() {
        if (clear_results_request.readyState === 4) {
            if (clear_results_request.status === 200 && clear_results_request.responseText === "success") {
                console.log("Clear results - success");
                results_list_element.innerHTML = "";
                if (logged_in) {
                    player_stats_element.innerHTML = "";
                }
            } else {
                console.log("Clear results - failed");
            }
        }
    }

    let clear_results_request = new XMLHttpRequest();
    clear_results_request.addEventListener("readystatechange", handleResponse, false);
    clear_results_request.open("POST", root + "/clear_results", true);
    clear_results_request.send();

    clear_results_element.className = "hidden";
}

function pause(event) {
    if (event.key === "Escape") {
        paused = true;
        sounds.music.pause();
        window.cancelAnimationFrame(request_id);
        welcome_element.innerHTML = "Game Paused";
        start_element.innerHTML = "Press any key to resume the game.";
        window.removeEventListener("keydown", pause, false);
        window.addEventListener("keydown", resume, false);
    }
}

function resume() {
    paused = false;
    sounds.music.play();
    welcome_element.innerHTML = "";
    start_element.innerHTML = "";
    window.removeEventListener("keydown", resume, false);
    window.addEventListener("keydown", pause, false);
    if (power_up_decrement.active) {
        decrementPowerUps();
    }
    draw();
}

function randInt(min, max) {
    return Math.round(Math.random() * (max - min)) + min;
}

function randIntFactor(min, max, factor) {
    let n = Math.round(Math.random() * (max - min)) + min;
    return n - (n % factor);
}