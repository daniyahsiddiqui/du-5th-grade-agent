const { Client, LocalAuth, MessageMedia } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const { execFile } = require('child_process');
const path = require('path');
const fs = require('fs');

const ENGINE_PATH = path.join(__dirname, '..', 'whatsapp_engine.py');
const REPORTS_DIR = path.join(__dirname, '..', 'reports');
const LATEST_HTML = path.join(REPORTS_DIR, 'latest_report.html');
const LATEST_PDF = path.join(REPORTS_DIR, 'latest_report.pdf');

console.log("============================================================");
console.log("🤖 DU 5th Grade WhatsApp Personal Account Bot Starting...");
console.log("============================================================");

// Clean up stale Chromium lock files if previous process crashed or was force-closed
const sessionDir = path.join(__dirname, '.wwebjs_auth', 'session-du_5th_grade_parent_bot');
const lockFiles = ['SingletonLock', 'SingletonSocket', 'SingletonCookie'];
lockFiles.forEach(file => {
    const lockPath = path.join(sessionDir, file);
    if (fs.existsSync(lockPath)) {
        try {
            fs.unlinkSync(lockPath);
            console.log(`[SESSION CLEANUP] Removed stale lock file: ${file}`);
        } catch (err) {
            // Ignored if busy
        }
    }
});

// Catch uncaught errors (such as page re-injection glitches during page reload) to prevent crash
process.on('uncaughtException', (err) => {
    if (err.message && err.message.includes('onQRChangedEvent')) {
        console.log("ℹ️ [NOTICE] Handled WhatsApp Web page binding refresh.");
    } else {
        console.error(`[PROCESS NOTICE] ${err.message}`);
    }
});

process.on('unhandledRejection', (reason, promise) => {
    // Ignore minor puppeteer binding rejections
});

const client = new Client({
    authStrategy: new LocalAuth({
        clientId: "du_5th_grade_parent_bot"
    }),
    puppeteer: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    }
});

const LATEST_PNG = path.join(REPORTS_DIR, 'latest_report.png');

async function getOrGenerateImage() {
    try {
        if (!client.pupBrowser) {
            return fs.existsSync(LATEST_PNG) ? LATEST_PNG : null;
        }
        console.log("[IMAGE] Rendering 1-page summary PNG card from latest_report.html...");
        const page = await client.pupBrowser.newPage();
        await page.setViewport({ width: 900, height: 1200, deviceScaleFactor: 2 });
        await page.goto('file://' + LATEST_HTML, { waitUntil: 'networkidle0' });
        await page.screenshot({ path: LATEST_PNG, fullPage: true });
        await page.close();
        console.log("[IMAGE SUCCESS] Saved: " + LATEST_PNG);
        return LATEST_PNG;
    } catch (err) {
        console.error(`[IMAGE GENERATION WARNING] ${err.message}`);
        return fs.existsSync(LATEST_PNG) ? LATEST_PNG : null;
    }
}

async function getOrGeneratePdf() {
    try {
        if (!client.pupBrowser) {
            return fs.existsSync(LATEST_PDF) ? LATEST_PDF : null;
        }
        console.log("[PDF] Rendering 1-page printable PDF from latest_report.html...");
        const page = await client.pupBrowser.newPage();
        await page.goto('file://' + LATEST_HTML, { waitUntil: 'networkidle0' });
        await page.pdf({
            path: LATEST_PDF,
            format: 'A4',
            printBackground: true,
            margin: { top: '10mm', right: '10mm', bottom: '10mm', left: '10mm' }
        });
        await page.close();
        console.log("[PDF SUCCESS] Saved: " + LATEST_PDF);
        return LATEST_PDF;
    } catch (err) {
        console.error(`[PDF GENERATION WARNING] ${err.message}`);
        return fs.existsSync(LATEST_PDF) ? LATEST_PDF : null;
    }
}

console.log("⏳ [1/2] Launching Chrome browser engine...");

if (fs.existsSync(sessionDir)) {
    console.log("ℹ️ [SESSION DETECTED] Restoring saved login session from disk...");
    console.log("👉 (If you want to re-scan a fresh QR code, run: ./start_whatsapp_bot.sh --reset)\n");
} else {
    console.log("ℹ️ [NEW SESSION] No saved login session found. Waiting for QR Code generation...\n");
}

client.on('loading_screen', (percent, message) => {
    console.log(`⏳ [STATUS] Loading WhatsApp Web: ${percent}% - ${message}`);
});

let isReady = false;

client.on('qr', (qr) => {
    console.log("\n============================================================");
    console.log("📱 SCAN THIS QR CODE WITH YOUR PERSONAL WHATSAPP PHONE");
    console.log("============================================================");
    console.log("Steps on your phone:");
    console.log("1. Open WhatsApp");
    console.log("2. Tap Settings (iOS) or 3 Dots Menu (Android)");
    console.log("3. Tap 'Linked Devices' -> 'Link a Device'");
    console.log("4. Point phone camera at terminal QR code below:\n");
    qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => {
    console.log("🔑 [STATUS] WhatsApp Authentication Successful!");
    console.log("⏳ [STATUS] Connecting to WhatsApp Web protocol...");

    // Watchdog timer: If protocol sync hangs for > 20s, clear stale session automatically
    setTimeout(async () => {
        if (!isReady) {
            console.log("\n⚠️ [SYNC NOTICE] Saved session is stuck loading. Resetting session cache automatically...");
            try {
                await client.destroy();
            } catch (e) {}
            try {
                fs.rmSync(sessionDir, { recursive: true, force: true });
            } catch (e) {}
            console.log("✅ Session cleared! Re-run './start_whatsapp_bot.sh' to scan a fresh QR code.");
            process.exit(0);
        }
    }, 20000);
});

client.on('auth_failure', (msg) => {
    console.error(`❌ [STATUS] Authentication Failed: ${msg}`);
});

client.on('ready', () => {
    isReady = true;
    console.log("\n============================================================");
    console.log("✅ [WHATSAPP BOT READY] Connected & Listening!");
    console.log("============================================================");
    console.log("The bot is now active in your WhatsApp groups.");
    console.log("Listen for commands: !due, !tests, !quran, !ixl, !spelling, !pdf, !all\n");
});

const CONFIG_PATH = path.join(__dirname, '..', 'config.json');

function getTargetGroupNames() {
    try {
        if (fs.existsSync(CONFIG_PATH)) {
            const cfg = JSON.parse(fs.readFileSync(CONFIG_PATH, 'utf8'));
            const target = cfg.whatsapp_group_name || "";
            if (!target) return [];
            return target.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
        }
    } catch (e) {
        console.log(`[CONFIG NOTICE] Using default group filter: ${e.message}`);
    }
    return [];
}

function extractChatName(chat) {
    if (!chat) return "";
    return chat.name || 
           chat.formattedTitle || 
           chat.subject || 
           (chat.groupMetadata && chat.groupMetadata.subject) || 
           "";
}

const recentCommands = new Map();

const replyToMessage = async (msg, content, options = {}) => {
    const targetChatId = (msg.from && (msg.from.endsWith('@g.us') || msg.from.endsWith('@c.us'))) 
        ? msg.from 
        : (msg.to && (msg.to.endsWith('@g.us') || msg.to.endsWith('@c.us'))) 
            ? msg.to 
            : (msg.from || msg.to);

    // For MessageMedia (images / PDFs), always fetch Chat object via getChatById first
    // to populate WhatsApp Web's memoized id property and avoid getter/getChat exceptions.
    if (content && (content instanceof MessageMedia || content.mimetype || options.caption)) {
        try {
            const chat = await client.getChatById(targetChatId);
            if (chat && typeof chat.sendMessage === 'function') {
                return await chat.sendMessage(content, options);
            }
        } catch (e) {
            console.error(`[MEDIA CHAT FETCH NOTICE] ${e.message}`);
        }
        return await client.sendMessage(targetChatId, content, options);
    }

    // For plain text messages, try msg.reply with fallback to client.sendMessage
    try {
        if (typeof msg.reply === 'function') {
            return await msg.reply(content, options);
        }
    } catch (e) {
        // Fallback for self-sent messages
    }
    return await client.sendMessage(targetChatId, content, options);
};

const handleIncomingMessage = async (msg) => {
    try {
        if (!msg || !msg.body) return;
        const text = msg.body.trim();
        const lowerText = text.toLowerCase();

        // Debug raw text arrival
        if (text.startsWith('!') || lowerText.includes('@bot') || lowerText.includes('due') || lowerText.includes('test') || lowerText.includes('pdf')) {
            console.log(`\n📩 [INCOMING RAW MSG] '${text}' (fromMe: ${msg.fromMe})`);
        }

        // CRITICAL GUARD: Never respond to bot's own generated responses or bot signature header!
        if (text.includes("DU 5th Grade") || 
            text.includes("🤖") || 
            text.includes("Weekly Overview") || 
            text.includes("Weekly IXL") ||
            text.includes("Upcoming Tests")) {
            return;
        }

        // 1. Quick check: Only process explicit user commands/keywords or @bot mentions
        const isPdfCommand = text.startsWith('!pdf') || 
                             text.startsWith('!report') || 
                             (lowerText.includes('@bot') && (lowerText.includes('pdf') || lowerText.includes('report') || lowerText.includes('printable'))) ||
                             lowerText === 'send pdf' || 
                             lowerText === 'get pdf' ||
                             lowerText === 'weekly pdf';

        const isCommand = isPdfCommand ||
                          text.startsWith('!') || 
                          lowerText.includes('@bot') ||
                          lowerText.includes('due tomorrow') || 
                          lowerText.includes('what is due') || 
                          lowerText.includes('upcoming test') || 
                          lowerText.includes('surah') || 
                          lowerText.includes('spelling list') || 
                          lowerText.includes('ixl homework');

        if (!isCommand) return;

        // Deduplication guard: ignore exact duplicate triggers within 4 seconds
        const now = Date.now();
        const key = `${msg.from}_${text}`;
        if (recentCommands.has(key) && (now - recentCommands.get(key)) < 4000) {
            return;
        }
        recentCommands.set(key, now);

        // 2. Group chat inspection
        let chatName = "";
        let isGroup = false;

        const groupId = (msg.from && msg.from.endsWith('@g.us')) ? msg.from :
                        (msg.to && msg.to.endsWith('@g.us')) ? msg.to : null;

        if (groupId) {
            isGroup = true;
            try {
                const chat = await msg.getChat();
                chatName = extractChatName(chat);
            } catch (e) {
                // Fallback
            }

            if (!chatName) {
                try {
                    const groupChat = await client.getChatById(groupId);
                    chatName = extractChatName(groupChat);
                } catch (e) {
                    // Fallback
                }
            }

            if (!chatName) {
                chatName = "Group Chat (" + groupId.split('@')[0] + ")";
            }
        } else {
            chatName = "Direct Message";
        }

        const targetGroups = getTargetGroupNames();

        if (isGroup && targetGroups.length > 0) {
            const matchesGroup = targetGroups.some(target => 
                target === "all" || 
                (chatName && chatName.toLowerCase().includes(target.toLowerCase())) ||
                chatName.startsWith("Group Chat") // Allow while metadata is syncing
            );
            if (!matchesGroup) {
                console.log(`[FILTERED] Ignored command in group '${chatName}' (target filter: ${targetGroups.join(', ')})`);
                return;
            }
        }

        console.log(`\n📩 [MSG DETECTED in '${chatName}'] '${text}' (fromMe: ${msg.fromMe})`);

        // Check if PDF or Report requested explicitly
        if (isPdfCommand) {
            console.log(`📄 [REPORT REQUEST] Sending weekly report digest to '${chatName}'...`);
            execFile('python3', [ENGINE_PATH, '!all'], async (error, stdout, stderr) => {
                const textDigest = stdout ? stdout.trim() : "⚠️ Sorry, could not generate report digest.";
                if (textDigest) {
                    await replyToMessage(msg, textDigest);
                    console.log(`✅ [TEXT DIGEST DISPATCHED SUCCESS] Sent text report to '${chatName}'!`);
                }
            });
            return;
        }

        // Query python whatsapp_engine.py
        execFile('python3', [ENGINE_PATH, text], async (error, stdout, stderr) => {
            if (error) {
                console.error(`[ENGINE ERROR] ${error.message}`);
                await replyToMessage(msg, "⚠️ Sorry, error generating response for homework query.");
                return;
            }

            const responseText = stdout.trim();
            if (responseText) {
                await replyToMessage(msg, responseText);
                console.log(`✅ [BOT REPLIED SUCCESS] Sent answer to '${chatName}'!`);
            }
        });

    } catch (err) {
        console.error(`[MSG ERROR] Safely handled message processing error: ${err.message}`);
    }
};

// Listen to both message and message_create so incoming group messages and self-test messages both trigger!
client.on('message', handleIncomingMessage);
client.on('message_create', handleIncomingMessage);

client.initialize();
