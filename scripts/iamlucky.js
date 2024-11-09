(function() {
    var mag = 3;
    var roll = Math.floor(Math.random() * 1000);

    while (roll === 0) {
        roll = Math.floor(Math.random() * 100);
        mag += 2;
    }

    var levelLoop = [2, 5, 10];
    var level = 0;
    var levelMag = 0;

    while ((Math.pow(10, mag) / (roll + 1)) >= levelLoop[level % 3] * Math.pow(10, levelMag)) {
        level++;
        levelMag = Math.floor(level / 3);
    }

    var desc = "";

    if (level > 0) {
        desc += "✅ Level " + level + ": 1/" +
                (levelLoop[(level - 1) % 3] * Math.pow(10, Math.floor((level - 1) / 3))) +
                " (" +
                (100 / (levelLoop[(level - 1) % 3] * Math.pow(10, Math.floor((level - 1) / 3)))).toFixed(Math.max(0, Math.floor((level - 1) / 3) - 1)) +
                "%) PASS\n";
    }

    desc += "❌ Level " + (level + 1) + ": 1/" +
            (levelLoop[level % 3] * Math.pow(10, levelMag)) +
            " (" +
            (100 / (levelLoop[level % 3] * Math.pow(10, levelMag))).toFixed(Math.max(0, levelMag - 1)) +
            "%) FAIL\n";

    desc += "\nYou rolled a 1 in " +
            (10 * mag / (roll + 1)).toFixed(3) +
            " chance. (" +
            ((roll + 1) / Math.pow(10, mag) * 100).toFixed(Math.max(0, mag - 2)) +
            "%)";

    if ((Math.pow(10, mag) / (roll + 1)) >= 1000) {
        return "POG LUCK HAPPENED!\n\n" + desc;
    }
    return desc;
})();
