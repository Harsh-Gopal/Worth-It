const fs = require('fs');

function replaceInFile(file, replacements) {
    let content = fs.readFileSync(file, 'utf8');
    for (const [from, to] of replacements) {
        content = content.replace(from, to);
    }
    fs.writeFileSync(file, content);
}

replaceInFile('src/hooks/useAlerts.ts', [
    ['import { AlertRule }', 'import type { AlertRule }']
]);

replaceInFile('src/hooks/useDealSearch.ts', [
    ['import { SearchRequest, SearchEvent, DealResult, Store }', 'import type { SearchRequest, SearchEvent, DealResult, Store }']
]);

replaceInFile('src/lib/api.ts', [
    ['import { AlertRule, AlertEvent, PriceObservation }', 'import type { AlertRule, AlertEvent, PriceObservation }']
]);

replaceInFile('src/components/alerts/AlertForm.tsx', [
    ['import { AlertRule }', 'import type { AlertRule }']
]);

replaceInFile('src/components/deals/DealCard.tsx', [
    ['import { DealResult }', 'import type { DealResult }'],
    ['import { ExternalLink, Tag, MapPin, Activity } from "lucide-react";\nimport clsx from "clsx";', 'import { ExternalLink, Tag, MapPin, Activity } from "lucide-react";']
]);

replaceInFile('src/components/deals/DealList.tsx', [
    ['import { DealResult }', 'import type { DealResult }'],
    ['import { Frown } from "lucide-react";', '']
]);

replaceInFile('src/components/search/SearchProgress.tsx', [
    ['import { SearchStatus, SearchMetrics }', 'import type { SearchStatus, SearchMetrics }'],
    ['import { CheckCircle2, Loader2, Map, AlertCircle, XCircle } from "lucide-react";', 'import { CheckCircle2, AlertCircle, XCircle } from "lucide-react";']
]);

replaceInFile('src/components/search/DealSearchForm.tsx', [
    ['import { SearchRequest }', 'import type { SearchRequest }'],
    ['const [strategy, setStrategy] = useState<"NEARBY_FIRST" | "FULL_RADIUS">("NEARBY_FIRST");', 'const [strategy] = useState<"NEARBY_FIRST" | "FULL_RADIUS">("NEARBY_FIRST");']
]);

replaceInFile('src/components/history/PriceHistoryChart.tsx', [
    ['import { PriceObservation }', 'import type { PriceObservation }'],
    ['(value: number) =>', '(value: any) =>']
]);

replaceInFile('src/components/map/DealMap.tsx', [
    ['import { Store, DealResult }', 'import type { Store, DealResult }']
]);

replaceInFile('src/pages/Alerts.tsx', [
    ['import { useAlerts } from "../../hooks/useAlerts";', 'import { useAlerts } from "../hooks/useAlerts";'],
    ['import type { AlertRule } from "../../lib/types";', 'import type { AlertRule } from "../lib/types";']
]);

replaceInFile('src/pages/DealRadar.tsx', [
    ['import { useDealSearch } from "../../hooks/useDealSearch";', 'import { useDealSearch } from "../hooks/useDealSearch";'],
    ['import { useAlerts } from "../../hooks/useAlerts";', 'import { useAlerts } from "../hooks/useAlerts";'],
    ['import DealSearchForm from "../../components/search/DealSearchForm";', 'import DealSearchForm from "../components/search/DealSearchForm";'],
    ['import SearchProgress from "../../components/search/SearchProgress";', 'import SearchProgress from "../components/search/SearchProgress";'],
    ['import DealList from "../../components/deals/DealList";', 'import DealList from "../components/deals/DealList";'],
    ['import DealMap from "../../components/map/DealMap";', 'import DealMap from "../components/map/DealMap";'],
    ['import AlertForm from "../../components/alerts/AlertForm";', 'import AlertForm from "../components/alerts/AlertForm";']
]);

console.log("Fixes applied");
