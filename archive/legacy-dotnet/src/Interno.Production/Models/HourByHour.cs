using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Production.Models
{
    public class HourByHour
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Hour { get; set; }
        //[Required]
        public int ResultId { get; set; }
        [Required]
        public string ResourceCode { get; set; }
        public string Item { get; set; }
        public double StdTime { get; set; }
        public int Meta { get; set; }
        public int Pieces { get; set; }
        public virtual double Attaiment { get { return (this.Meta != 0) ? this.Pieces / this.Meta : 0; } }
        public int EmployeesQty { get; set; }
        public double PaidHrs { get; set; }
        public virtual double GainedHrs { get { return (this.Pieces != 0 && this.StdTime != 0) ? this.Pieces * this.StdTime : 0; } }
        public virtual double Eficiency { get { return (this.GainedHrs / PaidHrs); } }
        public int Issues { get; set; }
        //[ForeignKey]
        [NotMapped]
        public virtual Result Result { get; set; }// Resource(Station),Shift
        [NotMapped]
        public virtual Resource Resource { get; set; }
        //public DateTime DowntimeD { get; set; }
        public virtual ICollection<Downtime> Downtimes { get; set; } = new List<Downtime>();
        public HourByHour()
        {
            Hour = DateTime.Now;
        }
    }
}