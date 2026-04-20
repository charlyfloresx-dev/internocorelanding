
import { Component, ElementRef, ViewChild, effect, input, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as d3 from 'd3';
import { ParetoItemDto } from '../../core/models/api.types';

@Component({
  selector: 'app-pareto-chart',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="w-full h-full relative">
      <div #chartContainer class="w-full h-[300px]"></div>
    </div>
  `
})
export class ParetoChartComponent implements OnDestroy {
  data = input.required<ParetoItemDto[]>();
  @ViewChild('chartContainer') chartContainer!: ElementRef;

  private resizeObserver: ResizeObserver | null = null;

  constructor() {
    effect(() => {
      const chartData = this.data();
      if (this.chartContainer && chartData.length > 0) {
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

  private createChart(data: ParetoItemDto[]) {
    if (!this.chartContainer) return;

    const element = this.chartContainer.nativeElement;
    d3.select(element).select('svg').remove();

    const margin = { top: 30, right: 40, bottom: 40, left: 50 };
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
      .padding(0.4)
      .domain(data.map(d => d.label));

    const xAxis = svg.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(x));

    xAxis.selectAll("text")
      .style("color", "#94a3b8")
      .style("font-size", "10px")
      .attr("transform", "rotate(-15)")
      .style("text-anchor", "end");
    
    xAxis.select(".domain").style("stroke", "#334155");
    xAxis.selectAll("line").remove();

    // Y Axis Left (Values)
    const yLeft = d3.scaleLinear()
      .domain([0, d3.max(data, d => d.value) || 100])
      .range([height, 0]);

    const yAxisLeft = svg.append('g').call(d3.axisLeft(yLeft).ticks(5));
    yAxisLeft.selectAll("text").style("color", "#64748b");
    yAxisLeft.select(".domain").remove();

    // Y Axis Right (Percentage)
    const yRight = d3.scaleLinear()
      .domain([0, 100])
      .range([height, 0]);

    const yAxisRight = svg.append('g')
      .attr("transform", `translate(${width}, 0)`)
      .call(d3.axisRight(yRight).ticks(5).tickFormat(d => d + "%"));
    
    yAxisRight.selectAll("text").style("color", "#fca5a5"); // Light Red
    yAxisRight.select(".domain").remove();

    // Bars
    svg.selectAll(".bar")
      .data(data)
      .enter().append("rect")
      .attr("class", "bar")
      .attr("x", d => x(d.label) || 0)
      .attr("width", x.bandwidth())
      .attr("y", height)
      .attr("height", 0)
      .attr("fill", "#0ea5e9") // Sky 500
      .attr("rx", 2)
      .transition()
      .duration(800)
      .attr("y", d => yLeft(d.value))
      .attr("height", d => height - yLeft(d.value));

    // Pareto Line
    const line = d3.line<ParetoItemDto>()
      .x(d => (x(d.label) || 0) + x.bandwidth() / 2)
      .y(d => yRight(d.cumulative))
      .curve(d3.curveMonotoneX);

    const path = svg.append("path")
      .datum(data)
      .attr("fill", "none")
      .attr("stroke", "#ef4444") // Red 500
      .attr("stroke-width", 2)
      .attr("d", line);

    // Animate Line
    const totalLength = path.node()?.getTotalLength() || 0;
    path.attr("stroke-dasharray", totalLength + " " + totalLength)
        .attr("stroke-dashoffset", totalLength)
        .transition()
        .delay(400)
        .duration(1200)
        .ease(d3.easeCubicOut)
        .attr("stroke-dashoffset", 0);

    // Points on Line
    svg.selectAll(".dot")
      .data(data)
      .enter().append("circle")
      .attr("cx", d => (x(d.label) || 0) + x.bandwidth() / 2)
      .attr("cy", d => yRight(d.cumulative))
      .attr("r", 3)
      .attr("fill", "#ef4444")
      .style("opacity", 0)
      .transition()
      .delay(1000)
      .style("opacity", 1);
      
    // Value Labels on Bars
    svg.selectAll(".label")
      .data(data)
      .enter().append("text")
      .text(d => d.value)
      .attr("x", d => (x(d.label) || 0) + x.bandwidth() / 2)
      .attr("y", d => yLeft(d.value) - 5)
      .attr("text-anchor", "middle")
      .style("fill", "white")
      .style("font-size", "10px")
      .style("opacity", 0)
      .transition()
      .delay(800)
      .style("opacity", 1);
  }
}
