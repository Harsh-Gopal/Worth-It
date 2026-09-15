const fs = require('fs');

function replaceInFile(file, replacements) {
    let content = fs.readFileSync(file, 'utf8');
    for (const [from, to] of replacements) {
        content = content.replace(from, to);
    }
    fs.writeFileSync(file, content);
}

replaceInFile('src/App.tsx', [
    ['import { Radar, Bell } from "lucide-react";', 'import { Radar } from "lucide-react";']
]);

replaceInFile('src/pages/Alerts.tsx', [
    ['alerts.map((alert) =>', 'alerts.map((alert: any) =>']
]);

console.log("Fixes applied");
