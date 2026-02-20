using System;
namespace Interno.DJO.Models
{
    public class EfficiencyHrs
    {
        public int Id { get; set; }
        public DateTime Date { get; set; }
        public int Hour { get{return this.Date.Hour;}}
        public int ResultId { get; set; }
        public virtual Interno.Production.Models.Result Result { get; set; }
        public string ResourceCode { get; set; }
        public virtual Interno.Inventory.Models.Warehouse Resource { get; set; }
        public string Item { get; set; }
        public double StdTime { get; set; }
        public int Meta { get; set; }
        public int Pieces { get; set; }
        public double Attaiment { get{ return (this.Meta != 0)? (this.Pieces*100) / this.Meta : 0; }}
        public int EmployeesQty { get; set; }
        public double PaidHrs { get; set;} 
        public double GainedHrs { get{  return (this.Pieces != 0 && this.StdTime != 0)? this.Pieces * this.StdTime :0; } }
        public double Eficiency { get{ return (this.PaidHrs > 0)?((this.GainedHrs) / PaidHrs)*100 : 0; } }
        public int Issues { get; set; }
        public DateTime Downtime { get; set; }
        public virtual Interno.Production.Models.Downtime ProdIssueDowntime { get; set; }

        public EfficiencyHrs(){
            this.Date = DateTime.Now;
        }
        
        public EfficiencyHrs(Interno.Production.Models.HourByHour hour)
        {
            this.Date = hour.Hour;
            this.ResultId = hour.ResultId;
            this.ResourceCode = hour.ResourceCode;
            this.Meta = hour.Meta;
            this.Pieces = this.Pieces;
        }
    }
}