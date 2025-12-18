import React from 'react';
import { StatCardProps } from '../types';

export const StatCard: React.FC<StatCardProps> = ({
  icon,
  iconBgColor,
  iconColor,
  title,
  value,
  subtext,
  subtextColor = "text-slate-500"
}) => {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-5 hover:shadow-md transition-shadow">
      <div className={`w-14 h-14 rounded-2xl flex items-center justify-center ${iconBgColor} ${iconColor} flex-shrink-0`}>
        {icon}
      </div>
      <div>
        <p className="text-sm font-medium text-slate-500 mb-1">{title}</p>
        <p className="text-2xl font-bold text-slate-900">{value}</p>
        {subtext && (
          <p className={`text-xs font-medium mt-1 ${subtextColor}`}>
            {subtext}
          </p>
        )}
      </div>
    </div>
  );
};