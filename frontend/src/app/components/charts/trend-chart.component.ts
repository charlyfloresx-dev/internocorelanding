
import { Component, ElementRef, ViewChild, effect, input, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as d3 from 'd3';
import { TrendPointDto } from '../../core/models/api.types';

@Component({
  selector: 'app-trend-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="w-full h-full relative">
      @if (data().length === 0) {
        <div class="absolute inset-0 flex items-center justify-center text-slate-500 text-xs">
           Sin datos de tendencia
        </div>
      }
      <div #chartContainer class="w-full h-[300px]"></div>
    </div>
  `
})
export class TrendChartComponent implements OnDestroy {
  data = input.required<TrendPointDto[]>();
  @ViewChild('chartContainer') chartContainer!: ElementRef;

  private resizeObserver: ResizeObserver | null = null;

  constructor() {
    effect(() => {
      const chartData = this.data();
      if (this.chartContainer) {
        setTimeout(() => this.createChart(chartData), 0);
      }
    });
  }

  ngAfterViewInit() {
    this.resizeObserver = new ResizeObserver(() => {
       this.createChart(this.data());
    });
    this.resizeObserver.observe(this.chartContainer.nativeElement);
  }

  ngOnDestroy() {
    if (this.resizeObserver) this.resizeObserver.disconnect();
  }

  private createChart(data: TrendPointDto[]) {
    if (!this.chartContainer) return;

    const element = this.chartContainer.nativeElement;
    d3.select(element).select('svg').remove();

    // GUARD: Prevent crash on empty data
    if (!data || data.length === 0) return;

    const margin = { top: 30, right: 30, bottom: 40, left: 40 };
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
    const x = d3.scalePoint()
      .domain(data.map(d => d.label))
      .range([0, width])
      .padding(0.5);

    const xAxis = svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x));
    
    xAxis.selectAll("text").style("color", "#94a3b8").style("font-size", "11px");
    xAxis.selectAll("line").remove();
    xAxis.select(".domain").style("stroke", "#334155");

    // Y Axis (Min 0, Max 100 or higher)
    const y = d3.scaleLinear()
      .domain([0, 110])
      .range([height, 0]);

    // Grid Lines
    svg.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(y).tickSize(-width).tickFormat(() => ''))
      .style("stroke-dasharray", ("3,3"))
      .style("color", "#334155")
      .style("opacity", 0.3);

    const yAxis = svg.append('g').call(d3.axisLeft(y).ticks(5));
    yAxis.selectAll("text").style("color", "#64748b");
    yAxis.select(".domain").remove();

    // Line Path
    const line = d3.line<TrendPointDto>()
      .x(d => x(d.label) || 0)
      .y(d => y(d.value))
      .curve(d3.curveMonotoneX);

    // Goal Line (Dashed)
    const goalLine = d3.line<TrendPointDto>()
      .x(d => x(d.label) || 0)
      .y(d => y(d.goal));

    svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#22c55e") // Green 500
      .attr("stroke-width", 2)
      .attr("stroke-dasharray", "4 4")
      .attr("d", goalLine)
      .style("opacity", 0.5);

    // Add Label for Goal (SAFE ACCESS)
    const firstItem = data[0]; // Guaranteed by Guard above
    if (firstItem) {
        svg.append("text")
          .attr("x", width)
          .attr("y", y(firstItem.goal) - 10)
          .attr("text-anchor", "end")
          .text(`Meta: ${firstItem.goal}%`)
          .style("fill", "#22c55e")
          .style("font-size", "10px");
    }

    // Actual Data Line
    const path = svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#0ea5e9") // Sky 500
      .attr("stroke-width", 3)
      .attr("d", line);

    // Animation for line
    const totalLength = path.node()?.getTotalLength() || 0;
    path.attr("stroke-dasharray", totalLength + " " + totalLength)
        .attr("stroke-dashoffset", totalLength)
        .transition()
        .duration(1500)
        .ease(d3.easeCubicOut)
        .attr("stroke-dashoffset", 0);

    // Dots
    svg.selectAll(".dot")
      .data(data)
      .enter().append("circle")
      .attr("cx", d => x(d.label) || 0)
      .attr("cy", d => y(d.value))
      .attr("r", 5)
      .attr("fill", "#0f172a") // Bg color
      .attr("stroke", "#0ea5e9")
      .attr("stroke-width", 2)
      .transition()
      .delay((d, i) => i * 100)
      .attr("r", 5);

    // Value Labels
    svg.selectAll(".label")
      .data(data)
      .enter().append("text")
      .text(d => d.value)
      .attr("x", d => x(d.label) || 0)
      .attr("y", d => y(d.value) - 10)
      .attr("text-anchor", "middle")
      .style("fill", "white")
      .style("font-size", "10px")
      .style("font-weight", "bold")
      .style("opacity", 0)
      .transition()
      .delay(1000)
      .style("opacity", 1);
  }
}
