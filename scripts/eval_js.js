const ivm = require('isolated-vm');

async function run() {
    // Create a new isolate with a memory limit
    const isolate = new ivm.Isolate({ memoryLimit: 128 });
    const context = await isolate.createContext();

    // Set up a secure jail
    const jail = context.global;
    await jail.set('global', jail.derefInto());

    // Create a safe console that only allows log
    const safeConsole = {
        log: (...args) => console.log(...args)
    };
    await jail.set('console', new ivm.Reference(safeConsole));

    const code = process.argv[2];
    try {
        // Run the code with a timeout
        const result = await context.eval(code, { timeout: 1000 });
        console.log(JSON.stringify(result));
    } catch (e) {
        console.error(JSON.stringify({ error: e.message }));
        process.exit(1);
    }
}

run();