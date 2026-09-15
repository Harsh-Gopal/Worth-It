import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import type { PriceObservation } from '../../lib/types';
import { TrendingDown, Minus } from 'lucide-react';

interface PriceHistoryChartProps {
  history: PriceObservation[];
}

export default function PriceHistoryChart({ history }: PriceHistoryChartProps) {
  if (!history || history.length < 2) {
    return (
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex flex-col items-center justify-center text-slate-400 gap-2 min-h-[200px]">
        <Minus className="w-8 h-8" />
        <span className="text-sm">Not enough price history yet.</span>
      </div>
    );
  }

  // Sort chronological for chart
  const data = [...history].reverse().map(obs => {
    const date = new Date(obs.timestamp);
    return {
      date: `${date.getDate()} ${date.toLocaleString('default', { month: 'short' })}`,
      price: obs.observed_price,
      mrp: obs.mrp,
      fullDate: date.toLocaleString()
    };
  });

  const lowestPrice = Math.min(...data.map(d => d.price));
  const currentPrice = data[data.length - 1].price;
  const isLowest = currentPrice <= lowestPrice;

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-semibold text-slate-800 flex items-center gap-2">
          Price History
          {isLowest && (
            <span className="text-[10px] uppercase font-bold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full flex items-center gap-1">
              <TrendingDown className="w-3 h-3" /> Historical Low
            </span>
          )}
        </h4>
        <div className="text-xs text-slate-500">
          Lowest: <span className="font-semibold text-slate-700">₹{lowestPrice}</span>
        </div>
      </div>
      
      <div className="h-[200px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: -20 }}>
            <XAxis 
              dataKey="date" 
              tick={{ fontSize: 10, fill: '#94a3b8' }} 
              axisLine={false} 
              tickLine={false} 
            />
            <YAxis 
              domain={['auto', 'auto']} 
              tick={{ fontSize: 10, fill: '#94a3b8' }}
              tickFormatter={(value) => `₹${value}`}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip 
              contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
              labelStyle={{ fontSize: '12px', fontWeight: 'bold', color: '#334155', marginBottom: '4px' }}
              itemStyle={{ fontSize: '12px' }}
              formatter={(value: any) => [`₹${value}`, 'Price']}
              labelFormatter={(label, payload) => payload?.[0]?.payload?.fullDate || label}
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke="#f43f5e" 
              strokeWidth={3}
              dot={{ r: 4, strokeWidth: 2, fill: '#fff' }}
              activeDot={{ r: 6, fill: '#f43f5e', stroke: '#fff', strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
