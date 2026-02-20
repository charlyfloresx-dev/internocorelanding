using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace Interno.DJO.Models
{
    public class ScoreCard
    {
        [Key]
        public int Id { get; set; }
        public string Partnership { get; set; }
        public string Category { get; set; }
        public string KPI { get; set; }
        public ReportFrecuency Frecuency { get; set; }
        public int Target { get; set; }
        public decimal FullScore { get; set; }
        public string CalculationMethod { get; set; }
        public string DataSource { get; set; }
        public string Link { get; set; }

        public virtual string FrecuencyReport { get{ return Enum.GetName(typeof(ReportFrecuency),this.Frecuency); }}
        public virtual ICollection<ScorePerformance> Performance { get; set;}
    }

    public class ScorePerformance
    {
        [Key]
        public int Id { get; set; }
        public DateTime Date { get; set; }
        public decimal Performance { get; set; }
        public decimal Score{ get; set; }
        public virtual ScoreCard ScoreCard { get; set;}
        public virtual string Period { get{return "P"+Date.Month;}}
        public virtual string Partnership { get; set;}
    }

    public enum ReportFrecuency
    {
        Weekly,
        Monthly,
        Quarterly,
        Yearly
    }
}