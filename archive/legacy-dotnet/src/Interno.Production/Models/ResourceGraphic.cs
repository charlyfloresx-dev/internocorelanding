using System;
using System.Collections.Generic;

namespace Interno.Production.Models
{
    public class ResourceGraphic
    {
        public List<TimeSpan> hours = new List<TimeSpan>();
        public  List<double> Disponible = new List<double>();
        public List<TimeSpan> Horas  = new List<TimeSpan>();
        public List<double> Descanzos = new List<double>();
        public List<double> Meta = new List<double>();
        public List<int> Producidas = new List<int>();
        public List<int> Faltante = new List<int>();
        public List<int> Excedente = new List<int>();
        public List<int> Acumulate = new List<int>();
        
        public List<int> Real = new List<int>();
        public List<int> RealAcumulate = new List<int>();
        public List<double> Eficiencia = new List<double>();
        public List<string> Categories = new List<string>();

        public List<Interno.Production.Models.Result> Plan = new List<Interno.Production.Models.Result>();

        public ICollection<Interno.HumanResource.Models.Catalog.Break> Breaks {get; set;}
    }   
}