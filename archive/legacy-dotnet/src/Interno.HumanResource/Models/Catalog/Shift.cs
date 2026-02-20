using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.HumanResource.Models.Catalog
{
     public class Shift
    {
        [Key]
        public int Id { get; set; }
        [MaxLength (13)]
        [Required]
        public string Code { get; set;}
        [Required]
        [DataType(DataType.Time)]
        public TimeSpan Start { get; set; }
        [Required]
        [DataType(DataType.Time)]
        public TimeSpan End { get; set; }
        [Required]
        [MaxLength(45)]
        public string Name { get; set; }
        [MaxLength(250)]
        public string Description { get; set; }
        public virtual ICollection<BreaksGroup> BreaksGroups { get; set; }
        //Calculo de Capacidades
        [DataType(DataType.Time)]
        public TimeSpan AvailableTime { get; set;}
        
        public virtual TimeSpan TotalTimeWorkday { 
            get{ 
                if(this.End < this.Start){return TimeSpan.FromTicks(TimeSpan.FromHours(24).Ticks + this.End.Ticks) - this.Start;
                }else{ return this.End - this.Start; }
            }
        }
        
        public virtual TimeSpan TotalTimeBreaks { get{ return TimeSpan.FromHours(1); } } //Tiempo total de Descanzos = SUM(Breaks)

        public virtual double Hours { get {return this.TotalTimeWorkday.TotalHours - this.TotalTimeBreaks.TotalHours;} }
        [NotMapped]
        public virtual DateTime DateStart { get{ return (this.Id == 1)? DateTime.Now.Date.AddTicks(this.Start.Ticks) :  
            (DateTime.Now.Hour < 6)? DateTime.Now.Date.AddDays(-1).AddTicks(this.Start.Ticks): DateTime.Now.Date.AddTicks(this.Start.Ticks); }}
        [NotMapped]
        public virtual DateTime DateEnd { get{ return this.DateStart.AddHours(12);} }
        
        
    }

    public class ShifGroupBrakes
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public int ShiftId { get; set; }
        public Shift Shift { get; set; }
        [Required]
        public int BreakGroupId { get; set; }
        public Interno.HumanResource.Models.Catalog.BreaksGroup BreakGroup { get; set; }
        [Required]
        public int BreakId { get; set; }
        public Break Break { get; set; }
    }
}