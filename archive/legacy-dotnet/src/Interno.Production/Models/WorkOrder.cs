using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

using Interno.Domain;

namespace Interno.Production.Models
{
    public class WorkOrder
    {
        public WorkOrder()
        {
            this.Guid = Guid.NewGuid();
            this.Results = new HashSet<Result>();
        }
        // {
        //     "0": "0",
        //     "assY$Item": "00-0772",
        //     "job Closed Date": "",
        //     "job Completed Date": "",
        //     "job Name": "V13839614",
        //     "job Quantity Completed": "0",
        //     "job Quantity Scheduled": "2000",
        //     "job Released Date": "2022-08-17 15:29:19",
        //     "job Scheduled Completion Dt": "2022-08-23 00:00:00",
        //     "job Status": "Released",
        //     "job Type": "Standard Discrete job",
        //     "organization Name": "TJM - Tijuana Manufacturing"
        // }

        [Key]
        [Required]
        public string Id { get; set; } //Numero de Registro
        [Required]
        public Guid Guid { get; set; }//Llave para identificar la Orden y llevar el control de cambios
        [Required]
        public virtual WOType Type { get; set; }//Typo de Orden de Produccion
        [Required]
        public string FinishItemCode { get; set; }
        //public virtual Interno.Inventory.Models.Item FinishItem { get; set; }
        [NotMapped]
        public int OperationTimeId { get; set; }
        public virtual OperationTime OperationTime{ get; set;}

        [MaxLength(45)]
        public string Alias { get; set; }
        //Qty
        //[Required]
        [MaxLength (4)]
        public string UMCode { get; set; }
        public virtual Interno.Domain.Catalog.UM UM { get; set; }
        [Required]
        public int OrderQty { get; set; }
        public int ManufQty { get; set; }
        public int Count { get; set; }
        public virtual int MissingQty { get{ return (this.OrderQty != this.Count)? this.OrderQty - (this.ManufQty+ this.Count): 0;} }
        //Status
        public virtual Interno.Domain.Enum.StatusType Status { get; set; }//Status de la Orden
        public virtual Interno.Domain.Enum.StatusType MaterialStatus { get; set; }//Status del Material
        //[Required]
        [MaxLength(5)]
        public string Review { get; set; }
        public long Lot { get; set; }
        public double Cost { get; set; }//Del Producto Final
        //Dates
        public DateTime Release {get; set;} //Fecha que se libero la Orden
        [Required]
        public DateTime Request { get; set; }//Fecha en que se require terminada la Orden
        public DateTime Start { get; set; }//Fecha de Inicio de Produccion
        public DateTime Finish { get; set; }//Fecha en que se termino

        //Times
        public TimeSpan Trascurred { get; set; }//Tiempo desde que se inicio la Orden y se termino de Producir
        public TimeSpan Downtime { get; set; }//Tiempo Muerto de la Orden

        //Estimated Values
        public TimeSpan EstimatedTime { get; set; }//Tiempo Estimado
        public double EstimatedCost { get; set; }//Costo Estimado

        //Approved
        public bool Approved { get; set; }//Orden Aprovada
        [MaxLength(100)]
        public string Responsible { get; set; }//Linea, Familia, Persona, Production Manager
        //[Required]
        [MaxLength(100)]
        public string Target { get; set; }//Linea, Familia, VSM
        //[Required]
        [MaxLength(100)]
        public string Planner { get; set; }//Planeador
        [MaxLength(250)]
        public string Comment { get; set; }
        [NotMapped]
        public int CustomerId { get; set; }
        public virtual Interno.Inventory.Models.Partnership Customer { get; set; }//Cliente

        //[TimestampAttribute ]
        [DatabaseGenerated(DatabaseGeneratedOption.Computed)]
        public DateTime Affected { get; set; }
        [NotMapped]
        public int RoutId { get; set; }

        public virtual Rout Rout { get; set; }
        [MaxLength(100)]
        public string Class { get; set; }

        /*** Important **/
        [NotMapped]
        public  ICollection<Result> Results { get; set; }

        public double Hours { get{ return (this.OperationTime != null)? this.OperationTime.SetTime.TotalHours * this.OrderQty : 0; }}
        public int WeekNumber { get{ return Interno.Domain.InternoExtensions.WeekOfYear(this.Affected) ; }}
        
    }

    public class ResultWorkOrder
    {
        public int ResultId { get; set; }
        public string WorkOrderId { get; set; }

        public Result Result { get; set; }
        public WorkOrder WorkOrder { get; set; }
    }

    public enum WOType //WorkOrderType
    {
        NonStandard,
        Standard,
        Repair,
        Rework,
        Test,
        Tooling,
        ScrapReplacement,
    }
}