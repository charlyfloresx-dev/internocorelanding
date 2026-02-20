using System.ComponentModel.DataAnnotations;

using Interno.Domain.Catalog;

namespace Interno.Security.Models
{
    public class VisitLog : SecurityLog
    {
        //Visitante
        [Required]
        public int PersonId { get; set; }
        public Interno.Domain.Catalog.Person Person {get; set;}
        
        //Visitado
        [Required]
        public int VisitingNumber { get; set; }
        public Interno.HumanResource.Models.Employee Visiting { get; set; }
        [Required]
        public string Subjet { get; set; }

        //Identificacion
        [Required]
        public int Badges { get; set; } //Gafete
        [Required]
        public IdentificationTypeEnum IdentifyType { get; set; }
        [Required]
        public string Identification { get; set; }
        //Vehiculo
        public VehicleTypeEnum VehicleType { get; set; }
        public string VehicleRegistration { get; set; }

        public string Comment { get; set; }
    }
}