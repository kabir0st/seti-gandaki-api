# Statement Statistics Visualization Guide

This guide explains how to visualize the statistics from the statements API endpoint in your frontend application.

## API Endpoint

```
GET /api/statements/statistics/
```

Query Parameters:
- `start_date` (optional): Start date in YYYY-MM-DD format
- `end_date` (optional): End date in YYYY-MM-DD format
- `period` (optional): Analysis period ('day', 'week', 'month', 'year'). Defaults to 'month'

## Data Structure

The API returns statistics for invoices, expenses, and purchase bills in the following format:

```json
{
  "invoices": {
    "total_count": 100,
    "total_amount": 50000.00,
    "average_amount": 500.00,
    "paid_count": 80,
    "pending_count": 15,
    "overdue_count": 5,
    "payment_stats": {
      "cash": 30,
      "bank": 60,
      "other": 10
    }
  },
  "expenses": {
    "total_count": 50,
    "total_amount": 15000.00,
    "average_amount": 300.00,
    "by_category": [
      {
        "category": "Office Supplies",
        "count": 20,
        "total": 5000.00
      }
    ],
    "payment_stats": {
      "cash": 20,
      "bank": 25,
      "other": 5
    }
  },
  "purchases": {
    "total_count": 75,
    "total_amount": 100000.00,
    "average_amount": 1333.33,
    "paid_count": 60,
    "pending_count": 15,
    "by_supplier": [
      {
        "supplier__name": "Supplier A",
        "count": 30,
        "total": 40000.00
      }
    ],
    "payment_stats": {
      "cash": 25,
      "bank": 45,
      "other": 5
    }
  },
  "period": {
    "start_date": "2024-03-01",
    "end_date": "2024-03-31"
  }
}
```

## Recommended Visualizations

### 1. Overview Dashboard

Create a dashboard with key metrics using cards:
- Total Invoices Amount
- Total Expenses Amount
- Total Purchase Amount
- Net Cash Flow (Invoices - Expenses - Purchases)

```typescript
// Example using React and Material-UI
import { Card, CardContent, Typography, Grid } from '@mui/material';

function OverviewDashboard({ data }) {
  const netCashFlow = data.invoices.total_amount - 
    data.expenses.total_amount - 
    data.purchases.total_amount;

  return (
    <Grid container spacing={3}>
      <Grid item xs={3}>
        <Card>
          <CardContent>
            <Typography variant="h6">Total Invoices</Typography>
            <Typography variant="h4">${data.invoices.total_amount}</Typography>
          </CardContent>
        </Card>
      </Grid>
      {/* Similar cards for expenses and purchases */}
    </Grid>
  );
}
```

### 2. Payment Status Charts

Use pie charts or donut charts to show:
- Invoice status distribution (Paid/Pending/Overdue)
- Payment method distribution for each type

```typescript
// Example using Chart.js
import { Doughnut } from 'react-chartjs-2';

function PaymentStatusChart({ invoiceData }) {
  const data = {
    labels: ['Paid', 'Pending', 'Overdue'],
    datasets: [{
      data: [
        invoiceData.paid_count,
        invoiceData.pending_count,
        invoiceData.overdue_count
      ],
      backgroundColor: ['#4CAF50', '#FFC107', '#F44336']
    }]
  };

  return <Doughnut data={data} />;
}
```

### 3. Time Series Analysis

Create line charts to show trends over time:
- Daily/Weekly/Monthly totals
- Running averages

```typescript
// Example using Recharts
import { LineChart, Line, XAxis, YAxis } from 'recharts';

function TrendChart({ data, period }) {
  return (
    <LineChart width={800} height={400} data={data}>
      <XAxis dataKey="date" />
      <YAxis />
      <Line type="monotone" dataKey="amount" stroke="#8884d8" />
    </LineChart>
  );
}
```

### 4. Category and Supplier Analysis

Use bar charts for:
- Expense categories breakdown
- Top suppliers by purchase amount

```typescript
// Example using Chart.js
import { Bar } from 'react-chartjs-2';

function CategoryChart({ expenseData }) {
  const data = {
    labels: expenseData.by_category.map(cat => cat.category),
    datasets: [{
      data: expenseData.by_category.map(cat => cat.total),
      backgroundColor: '#2196F3'
    }]
  };

  return <Bar data={data} />;
}
```

## Best Practices

1. **Responsive Design**
   - Ensure charts resize properly on different screen sizes
   - Use responsive grid layouts
   - Consider mobile-first approach

2. **Interactivity**
   - Add tooltips to show detailed information
   - Enable clicking on chart elements for drill-down views
   - Implement date range selectors

3. **Performance**
   - Implement data caching
   - Use lazy loading for charts
   - Consider using web workers for heavy calculations

4. **Accessibility**
   - Include proper ARIA labels
   - Provide table views as alternatives to charts
   - Ensure keyboard navigation

## Example Implementation

```typescript
// Example using React and TypeScript
import React, { useState, useEffect } from 'react';
import { Grid, Card, DatePicker } from '@mui/material';
import { fetchStatistics } from './api';

interface StatisticsProps {
  startDate?: string;
  endDate?: string;
}

export function StatisticsDashboard({ startDate, endDate }: StatisticsProps) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      try {
        const stats = await fetchStatistics(startDate, endDate);
        setData(stats);
      } catch (error) {
        console.error('Failed to load statistics:', error);
      }
      setLoading(false);
    };

    loadData();
  }, [startDate, endDate]);

  if (loading) return <LoadingSpinner />;
  if (!data) return <ErrorMessage />;

  return (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <OverviewDashboard data={data} />
      </Grid>
      <Grid item xs={12} md={6}>
        <PaymentStatusChart invoiceData={data.invoices} />
      </Grid>
      <Grid item xs={12} md={6}>
        <CategoryChart expenseData={data.expenses} />
      </Grid>
      {/* Add more visualization components */}
    </Grid>
  );
}
```

## Error Handling

Always implement proper error handling and loading states:
- Show loading spinners during data fetch
- Display error messages when API calls fail
- Provide fallback UI for empty data
- Include retry mechanisms for failed requests

## Data Refresh

Consider implementing:
- Automatic refresh intervals
- Manual refresh buttons
- Real-time updates using WebSocket if needed 