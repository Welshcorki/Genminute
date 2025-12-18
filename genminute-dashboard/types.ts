import React from 'react';

export interface NavItem {
  label: string;
  icon: React.ReactNode;
  id: string;
}

export interface StatCardProps {
  icon: React.ReactNode;
  iconBgColor: string;
  iconColor: string;
  title: string;
  value: string;
  subtext?: string;
  subtextColor?: string;
}

export enum Tab {
  HOME = 'home',
  MINUTES = 'minutes',
  RECORD = 'record'
}