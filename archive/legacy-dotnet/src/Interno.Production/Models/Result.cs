using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace Interno.Production.Models
{
    public class Result
    {
        public Result()
        {
            this.Orders = new HashSet<ResultWorkOrder>();
            this.HourByHour = new HashSet<HourByHour>();
            this.Labor = new HashSet<Labor>();
        }

        [Key]
        public int Id { get; set; }
        [Required]
        public int Priority { get; set; }
        //Dates
        [Required]
        public DateTime Date { get; set; }
        [Required]
        public string ResourceCode { get; set; }
        public virtual Resource Resource { get; set; }//Estacion, Linea, Celda //(Ares,Facility,Warehouse,Location,Address) - Modulo
        public string SubResourceCode { get; set; }
        public virtual Resource SubResource { get; set; } //Brazos, Lineas de apollo //Celda,Estacion
        [Required]
        public int ShiftId { get; set; }
        public virtual Interno.HumanResource.Models.Catalog.Shift Shift { get; set; }//Turno -> Breaks
        public virtual Interno.HumanResource.Models.Catalog.BreaksGroup Breaks { get; set; }//Segun el turno grupo de Descanzos
        //*** Important ***
        [NotMapped]
        public virtual ICollection<ResultWorkOrder> Orders { get; set; }//Numero de Orden de Trabajo
        [NotMapped]
        public virtual ICollection<Goal> Goals { get; set; }
        //Labor
        public virtual ICollection<Labor> Labor { get; set; }
        //Hour By Hour
        public virtual ICollection<HourByHour> HourByHour { get; set; }// Horas,Piezas //Cambiar por EfficiencyHrs
        [NotMapped]
        public virtual List<string> listOrder { get; set; }
        [NotMapped]
        public virtual ICollection<Tracking> Trackings { get; set; }//Trazabilidad Order, Proceso, Pernal
        public int Operators { get; set; }// Necesari Operation -> Operators == Labor -> Count(Operators)
        //Downtime
        public virtual ICollection<Downtime> Downtime { get; set; }
        public TimeSpan LeadTime { get; set; } //Suma de todos los tiempos muertos || SUM(Downtime)

        //Production Times
        [DataType(DataType.DateTime)]
        public DateTime InitialTime { get; set; } // Fecha y Tiempo que Inicia  Produccion
        public TimeSpan AvailableTime { get { return (this.Shift != null && this.Shift.End != TimeSpan.Zero) ? this.Shift.End - this.Shift.Start : TimeSpan.Zero; } } // Shift.End - InitialTime
        //Times
        public TimeSpan ScheduledStops { get; set; } //SS =` Descanzos + Mantenimientos + No se necesita Produccion (Paros Programados)
        public TimeSpan ProductiveTime { get; set; }// PT = SUM(tracking.SUM(Transcurred)) || NOW - InitialTime (Tiempo Produciendo)
        public TimeSpan ScheduledOperatingTime { get; set; } // SOT = SUM(Downtime)
        //public TimeSpan PlantOperatingTime { get; set; } = POT = Shift->End - Shift->Start
        public TimeSpan OperativeTime { get; set; } // ScheduledStops + ScheduledOperatingTime(Downtime) + ( ProductioveTime (Tiempo de Operacion) || Sum(HoutxHour->PaidHrs))
        public DateTime OverTimeEnd { get; set; }
        public TimeSpan OverTime { get; set; } // OverTimeEnd - Shift.End
        [NotMapped]
        public virtual OperationTime OperationTime { get; set; }

        public virtual TimeSpan PlanedTime { get; set; }

        //public double PaidHrs { get; set; }
        //public double GainsHrs { get; set; }

        //Calculate
        //[Required]
        public string Item { get; set; }
        public string Description { get; set; }
        //[Required]
        public string WorkOrder { get; set; }
        //[Required]
        public int OrderQty { get; set; } //OrderQty
        //[Required]
        public int PlanQty { get; set; }
        public int Actual { get; set; } // SUM(HourByHour.Pieces)
        public double Rate { get; set; } // Actual / ProductionTime.TotalHours

        public double OEE { get; set; } // ProductiveTime / ScheduledOperatingTime = Overal Equipment Efectiveness
        public double OE { get; set; } // ProductiveTime / OperativeTime = Operation Eficiency
        public double TEP { get; set; } // OperativeTime / ProductiveTime = Total Eficiency Performance

        public double Availability { get; set; } // ProductiveTime / AvailableTime
        public double Eficiency { get; set; } // OrderQty / Actual || PaidHrs / GainHrs
        public double FirstPassYield { get; set; } // Piezas Buenas / Piezas Producidas 
        public double OEE1 { get; set; } // Availability + Eficiency + FirstPassYield ?

        //Aditional Data
        public TimeSpan TakTime { get; set; }// ActualTime.TotalSeconds / Actual
        public double Capacity { get; set; }// AvailableTime / Taktime
        public double LMPU { get; set; }// Availabletime.TotalSeconds * Count(Operators) / OrderQty /60 = 4.42 seg
        public double Inprovement { get; set; }//= Average de LMPU Acumulado - LMPU 

        [Required]
        public DateTime ShippingDate { get; set; }
        [Required]
        public DateTime WHSDate { get; set; }
        [Required]
        public DateTime SMKTDate { get; set; }
        public DateTime Date1 { get; set; }
        public DateTime Date2 { get; set; }

        //Personal a Cargo
        public int LeaderNumber { get; set; }
        [NotMapped]
        public virtual Interno.HumanResource.Models.Employee Leader { get; set; }
        public int SupervisorNumber { get; set; }
        [NotMapped]
        public virtual Interno.HumanResource.Models.Employee Supervisor { get; set; }

        public string Planner { get; set; }

        //Data Info
        [DatabaseGenerated(DatabaseGeneratedOption.Identity)]
        public DateTime Created { get; set; } = DateTime.UtcNow;
        [TimestampAttribute]
        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Updated { get; set; } = DateTime.UtcNow;
    }
}