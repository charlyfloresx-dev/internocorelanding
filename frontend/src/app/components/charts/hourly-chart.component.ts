
import { Component, ElementRef, ViewChild, effect, input, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as d3 from 'd3';
import { ProductionStatDto } from '../../core/models/api.types';

@Component({
  selector: 'app-hourly-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="w-full h-full relative">
      <div #chartContainer class="w-full h-[300px]"></div>
    </div>
  `
})
export class HourlyChartComponent implements OnDestroy {
  data = input.required<ProductionStatDto[]>();
  @ViewChild('chartContainer') chartContainer!: ElementRef;

  private svg: any;
  private resizeObserver: ResizeObserver | null = null;

  constructor() {
    effect(() => {
      const chartData = this.data();
      if (this.chartContainer && chartData.length > 0) {
        // Simple debounce/delay to ensure container has width
        setTimeout(() => this.createChart(chartData), 0);
      }
    });
  }

  ngAfterViewInit() {
    // Add resize listener
    this.resizeObserver = new ResizeObserver(() => {
       this.createChart(this.data());
    });
    this.resizeObserver.observe(this.chartContainer.nativeElement);
  }

  ngOnDestroy() {
    if (this.resizeObserver) {
      this.resizeObserver.disconnect();
    }
  }

  private createChart(data: ProductionStatDto[]) {
    if (!this.chartContainer) return;

    const element = this.chartContainer.nativeElement;
    d3.select(element).select('svg').remove(); // Clear previous

    const margin = { top: 20, right: 20, bottom: 30, left: 40 };
    const width = element.offsetWidth - margin.left - margin.right;
    const height = element.offsetHeight - margin.top - margin.bottom;

    if (width <= 0 || height <= 0) return;

    const svg = d3.select(element)
      .append('svg')
      .attr('width', width + margin.left + margin.right)
      .attr('height', height + margin.top + margin.bottom)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // X Axis
    const x = d3.scaleBand()
      .range([0, width])
      .padding(0.5);
    
    x.domain(data.map(d => d.hour));
    
    // Axis styles for Dark Mode
    const xAxis = svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x));
      
    xAxis.selectAll("text")
      .style("color", "#94a3b8") // Slate 400
      .style("font-size", "11px");
    
    xAxis.selectAll("line").style("stroke", "#334155"); // Slate 700
    xAxis.select(".domain").style("stroke", "#334155");

    // Y Axis
    const y = d3.scaleLinear()
      .range([height, 0]);
    
    const maxVal = d3.max(data, d => Math.max(d.goal, d.actual)) || 100;
    y.domain([0, maxVal * 1.1]);

    // Custom Grid lines
    svg.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(y)
        .tickSize(-width)
        .tickFormat(() => '')
      )
      .style("stroke-dasharray", ("3,3"))
      .style("color", "#334155") // Slate 700 lines
      .style("opacity", 0.3);

    const yAxis = svg.append('g').call(d3.axisLeft(y).ticks(5));
    yAxis.selectAll("text").style("color", "#64748b"); // Slate 500
    yAxis.select(".domain").remove();

    // Bars (Actual)
    svg.selectAll('.bar')
      .data(data)
      .enter().append('rect')
      .attr('class', 'bar')
      .attr('x', d => x(d.hour) || 0)
      .attr('width', x.bandwidth())
      .attr('y', height) 
      .attr('height', 0)
      .attr('rx', 2)
      .attr('fill', d => {
        // Semantic Colors
        switch(d.status) {
          case 'excellent': return '#16a34a'; // Green 600
          case 'good': return '#0ea5e9'; // Sky 500
          case 'warning': return '#eab308'; // Yellow 500
          case 'critical': return '#ef4444'; // Red 500
          default: return '#0ea5e9';
        }
      })
      .transition()
      .duration(800)
      .attr('y', d => y(d.actual))
      .attr('height', d => height - y(d.actual));

    // Goal Markers (Line)
    svg.selectAll('.goal-line')
      .data(data)
      .enter().append('line')
      .attr('x1', d => (x(d.hour) || 0) - 2)
      .attr('x2', d => (x(d.hour) || 0) + x.bandwidth() + 2)
      .attr('y1', d => y(d.goal))
      .attr('y2', d => y(d.goal))
      .attr('stroke', '#cbd5e1') // Slate 300
      .attr('stroke-width', 2)
      .style('opacity', 0)
      .transition()
      .delay(500)
      .duration(500)
      .style('opacity', 0.8);
      
    // Text labels on bars
    svg.selectAll('.label')
      .data(data)
      .enter().append('text')
      .text(d => d.actual)
      .attr('x', d => (x(d.hour) || 0) + x.bandwidth() / 2)
      .attr('y', d => y(d.actual) - 6)
      .attr('text-anchor', 'middle')
      .style('fill', '#e2e8f0') // Slate 200
      .style('font-weight', '600')
      .style('font-size', '10px')
      .style('opacity', 0)
      .transition()
      .delay(600)
      .duration(300)
      .style('opacity', 1);
  }
}
