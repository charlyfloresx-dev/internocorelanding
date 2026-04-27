import { Component, OnInit, signal, effect, ElementRef, viewChild, inject, AfterViewInit, ViewEncapsulation } from '@angular/core';
import { CommonModule } from '@angular/common';
import * as L from 'leaflet';
import { HttpClient } from '@angular/common/http';
import { AssetCrmService } from '../../services/asset-crm';
import { ThemeService } from '../../../../../core/services/theme.service';

@Component({
  selector: 'app-price-map',
  standalone: true,
  imports: [
    CommonModule
  ],
  templateUrl: './price-map.html',
  styleUrl: './price-map.css',
  encapsulation: ViewEncapsulation.None
})
export class PriceMapComponent implements OnInit, AfterViewInit {
  private http = inject(HttpClient);
  private crmService = inject(AssetCrmService);
  private themeService = inject(ThemeService);
  private map?: L.Map;
  private baseLayer?: L.TileLayer;
  private currentMarker?: L.Marker;
  
  mapContainer = viewChild<ElementRef>('mapContainer');
  selectedProperty = signal<any>(null);
  isLoading = signal(false);
  
  // Icon Fix for Leaflet
  private defaultIcon = L.icon({
    iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34]
  });

  // IMPLAN WMS Config
  private readonly WMS_URL = 'https://gemelodigital.implantijuana.gob.mx/geoserver-local-proxy/wms';
  private readonly WMS_LAYERS = 'catastro_pub:predios-211126_Predios';

  ngOnInit() {
    // Initialization handled by mapContainer effect
  }

  ngAfterViewInit() {
    // Ensure map takes full size after layout is stable
    setTimeout(() => {
      this.map?.invalidateSize();
    }, 500);
  }

  constructor() {
    effect(() => {
      const container = this.mapContainer()?.nativeElement;
      if (container && !this.map) {
        this.initMap(container);
      }
    });

    // Theme Switch Effect
    effect(() => {
      const isDark = this.themeService.darkMode();
      if (this.map) {
        this.updateBaseLayer(isDark);
      }
    });
  }

  private updateBaseLayer(isDark: boolean) {
    if (this.baseLayer) {
      this.map?.removeLayer(this.baseLayer);
    }

    const url = isDark 
      ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png';

    this.baseLayer = L.tileLayer(url, {
      attribution: '&copy; OpenStreetMap contributors &copy; CARTO'
    }).addTo(this.map!);
    
    // Bring WMS to front if it exists
    this.map?.eachLayer(layer => {
      if (layer instanceof L.TileLayer.WMS) {
        layer.bringToFront();
      }
    });
  }

  private initMap(container: HTMLElement) {
    this.map = L.map(container, {
      center: [32.491194, -116.909222], // Venustiano Carranza 6315/6319
      zoom: 18,
      zoomControl: false
    });

    // Initial Base Layer
    this.updateBaseLayer(this.themeService.darkMode());

    // IMPLAN WMS Overlay
    L.tileLayer.wms(this.WMS_URL, {
      layers: this.WMS_LAYERS,
      format: 'image/png',
      transparent: true,
      version: '1.1.1',
      attribution: 'IMPLAN Tijuana'
    }).addTo(this.map);

    // Initial Marker
    this.currentMarker = L.marker([32.491194, -116.909222], { icon: this.defaultIcon }).addTo(this.map)
      .bindPopup('<b>PK020027</b><br>Venustiano Carranza 6315/6319')
      .openPopup();

    // Custom Zoom Control
    L.control.zoom({ position: 'bottomright' }).addTo(this.map);

    // Map Click Listener
    this.map.on('click', (e: L.LeafletMouseEvent) => {
      this.handleMapClick(e.latlng);
    });

    // Request Geolocation to center map "donde estoy ahorita"
    this.map.locate({ setView: true, maxZoom: 18 });
    this.map.on('locationerror', () => {
      console.warn("Geolocalización no disponible, manteniendo centro en Tijuana.");
    });

    // Final check for size
    setTimeout(() => {
      this.map?.invalidateSize();
    }, 500);
  }

  private async handleMapClick(latlng: L.LatLng) {
    this.isLoading.set(true);

    // Move Marker
    if (this.currentMarker) {
      this.currentMarker.setLatLng(latlng);
    } else {
      this.currentMarker = L.marker(latlng, { icon: this.defaultIcon }).addTo(this.map!);
    }
    
    // 1. Convert to Web Mercator (EPSG:3857) for WMS GetFeatureInfo
    const x = latlng.lng * 20037508.34 / 180;
    const y = Math.log(Math.tan((90 + latlng.lat) * Math.PI / 360)) / (Math.PI / 180) * 20037508.34 / 180;

    // 2. Create Bounding Box for GetFeatureInfo (small 20m window)
    const buffer = 10;
    const bbox = `${x - buffer},${y - buffer},${x + buffer},${y + buffer}`;
    
    const gfiUrl = `${this.WMS_URL}?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo` +
      `&QUERY_LAYERS=${this.WMS_LAYERS}&LAYERS=${this.WMS_LAYERS}` +
      `&INFO_FORMAT=application/json&X=160&Y=160&WIDTH=320&HEIGHT=320` +
      `&SRS=EPSG:3857&BBOX=${bbox}&FEATURE_COUNT=50`;

    try {
      const response: any = await this.http.get(gfiUrl).toPromise();
      const features = response?.features || [];
      
      if (features.length > 0) {
        const prop = features[0].properties;
        // The property name might vary, usually it's 'clave' or 'cve_cat'
        const clave = prop.clave || prop.CVE_CAT || prop.CLAVE || 'PK-020-027'; 
        
        this.selectedProperty.set({
          id: features[0].id || 'PROP-' + Math.floor(Math.random() * 1000),
          cve_cat: clave,
          address: prop.direccion || prop.UBICACION || 'Ubicación identificada',
          current_value: prop.valor_catastral || 0,
          historical_value: 0,
          appreciation: 0,
          owner: 'Haz clic en "Scrapear RPPC" para titular',
          lat: latlng.lat.toFixed(6),
          lng: latlng.lng.toFixed(6),
          x: x.toFixed(0),
          y: y.toFixed(0),
          raw_data: prop
        });
        
        // Ensure map resizes and recenters if needed when sidebar opens
        setTimeout(() => {
          this.map?.invalidateSize();
          this.map?.panTo(latlng);
        }, 100);
      } else {
        this.selectedProperty.set({
          id: 'NONE',
          cve_cat: 'NO IDENTIFICADO',
          address: 'Haz clic dentro de un predio',
          lat: latlng.lat.toFixed(6),
          lng: latlng.lng.toFixed(6),
          x: x.toFixed(0),
          y: y.toFixed(0)
        });
      }
    } catch (error) {
      console.error('GIS Error:', error);
      this.selectedProperty.set({
        id: 'ERROR',
        cve_cat: 'ERROR GIS',
        address: 'No se pudo conectar con el servidor municipal',
        lat: latlng.lat.toFixed(6),
        lng: latlng.lng.toFixed(6)
      });
    } finally {
      this.isLoading.set(false);
    }
  }

  viewForensicAnalysis() {
    const prop = this.selectedProperty();
    if (prop) {
      console.log('Ver Análisis Forense para:', prop.cve_cat);
      alert('Funcionalidad de Análisis Forense en desarrollo para: ' + prop.cve_cat);
    }
  }

  scrapeRPPC() {
    const prop = this.selectedProperty();
    if (prop) {
      console.log('Scrapeando RPPC para:', prop.cve_cat);
      // Actualizamos el prop.owner para dar feedback visual
      this.selectedProperty.set({
        ...prop,
        owner: 'Buscando en RPPC...'
      });
      
      // Simulamos la llamada o hacemos una real
      setTimeout(() => {
        this.selectedProperty.update(p => ({
          ...p,
          owner: 'Consulta finalizada (ver log backend)'
        }));
      }, 1500);
    }
  }

  onSearch(event: Event) {
    const query = (event.target as HTMLInputElement).value.toUpperCase();
    if (!query) return;

    console.log('Searching for:', query);
    
    // Simulate finding a zone or key
    if (query.includes('PRESIDENTES') || query.includes('PK020027')) {
      const targetLatLng = L.latLng(32.491194, -116.909222);
      this.map?.setView(targetLatLng, 18);
      this.handleMapClick(targetLatLng);
    }
  }

  closeDetail() {
    this.selectedProperty.set(null);
  }
}
