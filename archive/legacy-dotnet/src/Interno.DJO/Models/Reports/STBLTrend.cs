using System;
using System.ComponentModel.DataAnnotations;
using Interno.DJO.Helpers;
namespace Interno.DJO.Models
{   
    public class STBLTrend
    {
        [Key]
        public DateTime Date { get; set;}
        public int MFG { get; set; }
        public int PFG { get; set; }
        public int Total { get{return  this.MFG + this.PFG;}  set{ Total = this.MFG + this.PFG;} }
        public int Target { get; set; }
        public int Year { get{ return this.Date.Year;} }
        public int Week { get{ return this.Date.WeekOfYear();}}
    }
}