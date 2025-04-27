import {Component, ElementRef, ViewChild} from '@angular/core';
import {HttpClient} from '@angular/common/http';
import {CommonModule} from '@angular/common';
import {
  Chart,
  BarController,
  BarElement,
  LinearScale,
  CategoryScale,
  Tooltip,
  Legend,
  PieController,
  ArcElement,
  LineController,
  LineElement,
  PointElement,
  Title
} from 'chart.js';
import {FormsModule} from "@angular/forms";

@Component({
  selector: 'app-statistics',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './statistics.component.html',
  styleUrl: './statistics.component.css'
})
export class StatisticsComponent {
  @ViewChild('mainChart') mainChartRef!: ElementRef<HTMLCanvasElement>;
  private chart!: Chart;
  public yearInput: number = new Date().getFullYear();
  public isChartVisible: boolean = false;
  public chartOption: number | null = null;

  constructor(private http: HttpClient) {
    Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend, Title, PieController,
      ArcElement, LineController, LineElement, PointElement);
  }

  public showChart(option: number) {
    this.isChartVisible = true;
    this.chartOption = option;
    if (this.chart) {
      this.chart.destroy();
    }

    if (option === 1) {
      this.loadOrdersPerMonth();
    } else if (option === 2) {
      this.loadEarningsPerMonth();
    } else if (option === 3) {
      this.loadPublisherDistribution();
    }
  }

  public onYearChange() {
    this.showChart(this.chartOption!);
  }

  private loadOrdersPerMonth() {
    this.http.get<any>(`http://localhost:3050/stats/orders-per-month?year=${this.yearInput}`)
      .subscribe(response => {
        const data = response.data;
        const ctx = this.mainChartRef.nativeElement.getContext('2d');
        if (ctx) {
          const months = Array.from({length: 12}, (_, i) => (i + 1).toString().padStart(2, '0'));
          const ordersPerMonth: { [key: string]: number } = {};
          months.forEach(month => ordersPerMonth[month] = 0);

          data.forEach((item: any) => {
            const monthNumber = item.month.split('-')[1];
            ordersPerMonth[monthNumber] = item.orderCount;
          });

          this.chart = new Chart(ctx, {
            type: 'bar',
            data: {
              labels: months,
              datasets: [{
                label: 'Orders per Month',
                data: months.map(m => ordersPerMonth[m]),
                backgroundColor: 'rgba(30,144,255,0.7)',
                borderColor: 'blue',
                borderWidth: 1
              }]
            },
            options: {
              responsive: true,
              plugins: {
                title: {
                  display: true,
                  text: 'Orders Distribution Over the Year'
                }
              }
            }
          });
        }
      });
  }

  private loadEarningsPerMonth() {
    this.http.get<any>(`http://localhost:3050/stats/earnings-per-month?year=${this.yearInput}`)
      .subscribe(response => {
        const ctx = this.mainChartRef.nativeElement.getContext('2d');
        if (ctx) {
          const data = response.data;

          const labels = data.map((item: any) => item.month);
          const earnings = data.map((item: any) => item.earnings);

          if (this.chart) {
            this.chart.destroy();
          }

          this.chart = new Chart(ctx, {
            type: 'line',
            data: {
              labels: labels,
              datasets: [{
                label: 'Earnings per Month',
                data: earnings,
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 2,
                fill: true,
                tension: 0.4
              }]
            },
            options: {
              responsive: true,
              plugins: {
                title: {
                  display: true,
                  text: 'Earnings Distribution Over the Year'
                }
              },
              scales: {
                y: {
                  beginAtZero: true
                }
              }
            }
          });
        }
      });
  }

  private loadPublisherDistribution() {
    this.http.get<any>(`http://localhost:3050/stats/publisher-distribution`)
      .subscribe(response => {
        const ctx = this.mainChartRef.nativeElement.getContext('2d');
        if (ctx) {
          const data = response.data;

          const labels = data.map((item: any) => item.publisher);
          const counts = data.map((item: any) => item.booksCount);

          if (this.chart) {
            this.chart.destroy();
          }

          this.chart = new Chart(ctx, {
            type: 'pie',
            data: {
              labels: labels,
              datasets: [{
                data: counts,
                backgroundColor: [
                  'rgba(255,99,132,0.7)',
                  'rgba(54,162,235,0.7)',
                  'rgba(255,206,86,0.7)',
                  'rgba(75,192,192,0.7)',
                  'rgba(153,102,255,0.7)',
                  'rgba(255,159,64,0.7)',
                  'rgba(60,179,113,0.7)',
                  'rgba(255,99,71,0.7)',
                  'rgba(153,204,255,0.7)',
                  'rgba(128,0,128,0.7)',
                  'rgba(99,97,98,0.7)',
                ],
                borderColor: [
                  'rgba(255,99,132,1)',
                  'rgba(54,162,235,1)',
                  'rgba(255,206,86,1)',
                  'rgba(75,192,192,1)',
                  'rgba(153,102,255,1)',
                  'rgba(255,159,64,1)',
                  'rgba(60,179,113,1)',
                  'rgba(255,99,71,1)',
                  'rgba(153,204,255,1)',
                  'rgba(128,0,128,1)',
                  'rgba(99,97,98,1)',
                ],
                borderWidth: 1
              }]
            },
            options: {
              responsive: true,
              plugins: {
                title: {
                  display: true,
                  text: 'Publisher Distribution'
                }
              }
            }
          });
        }
      });
  }
}
